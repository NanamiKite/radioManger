#!/usr/bin/env python3
"""Exercise a disposable RadioManager installation, never a user's real database.

--state stores credentials and expected records (mode 0600); keep it out of artifacts.
--verify-state logs in afresh and checks those records without registering another user.
--websocket additionally needs websockets==16.0 and saves a real QSO over the UDP WS.
There are only two sensitive requests on creation and one on verification (limit: 5/min).
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import secrets
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener, ProxyHandler


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Client:
    def __init__(self, url):
        self.url = url.rstrip("/") + "/"
        self.token = None
        # Local smoke traffic must not inherit runner HTTP proxy settings.
        self.opener = build_opener(ProxyHandler({}))

    def request(self, path, data=None, status=200):
        headers = {"Accept": "*/*", "User-Agent": "RadioManager-CI-smoke"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        request = Request(urljoin(self.url, path.lstrip("/")), body, headers)
        try:
            response = self.opener.open(request, timeout=20)
        except HTTPError as error:
            response = error
        with response:
            content = response.read()
            require(response.status == status,
                    f"{request.get_method()} {path}: expected HTTP {status}, got {response.status}")
            return response.headers, content

    def json(self, path, data=None, status=200):
        headers, content = self.request(path, data, status)
        require("application/json" in headers.get("Content-Type", ""), f"{path}: not JSON")
        return json.loads(content)


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        value = attrs.get("src") if tag == "script" else attrs.get("href") if tag == "link" else None
        if value:
            asset = urljoin("/", value)
            if urlsplit(asset).path.startswith("/assets/"):
                self.urls.append(asset)


def check_serving(client, args):
    health = client.json("/health")
    require(health.get("status") == "ok", "health is not ok")
    require(health.get("database") == args.mode, "wrong database mode")
    require(health.get("version") == args.version, "wrong backend version")
    require(health.get("subsystems", {}).get("database") == "ok", "database health failed")
    headers, root = client.request("/")
    require("text/html" in headers.get("Content-Type", ""), "root does not serve HTML")
    require(b'id="app"' in root, "root lacks SPA mount")
    assets = Assets()
    assets.feed(root.decode("utf-8"))
    require(assets.urls, "root references no built static assets")
    for asset in assets.urls:
        parsed = urlsplit(asset)
        require(not parsed.netloc and not parsed.scheme, "static asset is not local")
        headers, content = client.request(asset)
        require(content and content != root and "text/html" not in headers.get("Content-Type", ""),
                f"{asset}: missing static content or SPA fallback")
    headers, deep = client.request("/logs")
    require("text/html" in headers.get("Content-Type", "") and deep == root,
            "History deep-link does not serve the SPA")
    for path in ("/api/v1/ci-missing-" + secrets.token_hex(6),
                 "/assets/ci-missing-" + secrets.token_hex(6) + ".js"):
        _, content = client.request(path, status=404)
        require(b'id="app"' not in content and content != root, f"{path}: returned SPA on missing resource")


def login(client, state):
    result = client.json("/api/v1/auth/login", {"username": state["username"], "password": state["password"]})
    require(result.get("token_type") == "Bearer" and result.get("access_token"), "missing bearer token")
    require(result["user"]["id"] == state["user_id"] and result["user"]["username"] == state["username"],
            "login returned wrong user")
    client.token = result["access_token"]
    me = client.json("/api/v1/auth/me")
    require(me["id"] == state["user_id"] and me["email"] == state["email"], "authenticated profile mismatch")


def matches(actual, expected, label):
    for key, value in expected.items():
        require(actual.get(key) == value, f"{label}: mismatched {key}")


async def websocket_save(client, payload):
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed

    parsed = urlsplit(urljoin(client.url, "api/v1/udp/ws"))
    url = urlunsplit(("wss" if parsed.scheme == "https" else "ws", parsed.netloc, parsed.path, "", ""))
    # A handshake alone isn't authentication: assert invalid credentials are rejected.
    async with connect(url, open_timeout=15, close_timeout=5, proxy=None) as ws:
        await ws.send(json.dumps({"token": "invalid-ci-token"}))
        try:
            await asyncio.wait_for(ws.recv(), timeout=10)
        except ConnectionClosed as error:
            require(error.code == 4401, "WS invalid auth returned wrong close code")
        else:
            raise RuntimeError("WS accepted invalid authentication")
    async with connect(url, open_timeout=15, close_timeout=5, proxy=None) as ws:
        await ws.send(json.dumps({"token": client.token}))
        await ws.send(json.dumps({"action": "save", "data": payload}))
        result = json.loads(await asyncio.wait_for(ws.recv(), timeout=20))
        require(result.get("type") == "qso_saved", "authenticated WS save failed")
        require(result["data"]["call_sign"] == payload["call_sign"], "WS saved wrong callsign")
        return result["data"]["id"]

def create(client, args):
    suffix = secrets.token_hex(8)
    state = {"username": "ci_" + suffix, "email": "ci_" + suffix + "@example.com",
             "password": secrets.token_urlsafe(24), "mode": args.mode, "version": args.version}
    registered = client.json("/api/v1/auth/register", {
        "username": state["username"], "email": state["email"], "password": state["password"],
        "confirm_password": state["password"]}, status=201)
    matches(registered, {"username": state["username"], "email": state["email"], "is_active": True}, "registration")
    state["user_id"] = registered["id"]
    login(client, state)
    station = client.json("/api/v1/stations", {"callsign": "W1CI"}, status=201)
    state["station"] = {"id": station["id"], "callsign": "W1CI", "user_id": state["user_id"]}
    matches(station, state["station"], "station creation")
    location = client.json("/api/v1/locations", {
        "station_id": station["id"], "name": "CI " + suffix, "grid_square": "FN31PR", "qth": "CI isolated site"}, status=201)
    state["location"] = {"id": location["id"], "station_id": station["id"], "user_id": state["user_id"],
                         "name": "CI " + suffix, "grid_square": "FN31PR", "qth": "CI isolated site", "is_active": True}
    matches(location, state["location"], "location creation")
    payload = {"station_id": station["id"], "location_id": location["id"], "call_sign": "K1ABC",
               "qso_date": "2026-01-02", "time_on": "03:04:05", "band": "20m", "mode": "SSB",
               "rst_sent": "59", "rst_rcvd": "57", "grid_square": "FN42", "comment": "ci-" + suffix}
    qso = client.json("/api/v1/logs", payload, status=201)
    expected = {**payload, "id": qso["id"], "my_gridsquare": "FN31PR", "station_callsign": "W1CI"}
    matches(qso, expected, "QSO creation")
    state["qsos"] = [expected]
    if args.websocket:
        ws_payload = {**payload, "call_sign": "K2ABC", "comment": "ws-" + suffix}
        ws_id = asyncio.run(websocket_save(client, ws_payload))
        state["qsos"].append({**ws_payload, "id": ws_id, "my_gridsquare": "FN31PR", "station_callsign": "W1CI"})
    return state


def verify(client, state):
    matches(client.json(f'/api/v1/stations/{state["station"]["id"]}'), state["station"], "saved station")
    locations = client.json("/api/v1/locations")
    require(len(locations) == 1, "wrong saved location count")
    matches(locations[0], state["location"], "saved location")
    listing = client.json("/api/v1/logs")
    require(listing["total"] == len(state["qsos"]) and len(listing["items"]) == len(state["qsos"]), "wrong saved QSO count")
    for expected in state["qsos"]:
        matches(client.json(f'/api/v1/logs/{expected["id"]}'), expected, "saved QSO")
        listed = next((item for item in listing["items"] if item["id"] == expected["id"]), None)
        require(listed is not None, "QSO missing from listing")
        matches(listed, expected, "listed QSO")
    query = urlencode({"station_id": state["station"]["id"], "location_id": state["location"]["id"]})
    headers, content = client.request("/api/v1/logs/export?" + query)
    require("attachment;" in headers.get("Content-Disposition", "") and ".adi" in headers.get("Content-Disposition", ""), "missing ADIF download header")
    text = content.decode("utf-8")
    require(len(re.findall(r"<eor>", text, re.I)) == len(state["qsos"]), "wrong ADIF record count")
    for qso in state["qsos"]:
        record = next((part for part in re.split(r"<eor>", text, flags=re.I)
                       if f'<call:{len(qso["call_sign"])}>{qso["call_sign"]}' in part), None)
        require(record is not None, "QSO missing from ADIF")
        for key, value in {"qso_date": "20260102", "time_on": "030405", "mode": "SSB", "band": "20m",
                           "station_callsign": "W1CI", "my_gridsquare": "FN31PR", "comment": qso["comment"]}.items():
            require(f"<{key}:{len(value)}>{value}" in record, f"ADIF mismatched {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--mode", choices=("sqlite", "mysql"), required=True)
    parser.add_argument("--version", required=True)
    state_args = parser.add_mutually_exclusive_group()
    state_args.add_argument("--state", type=Path)
    state_args.add_argument("--verify-state", type=Path)
    parser.add_argument("--websocket", action="store_true", help="also authenticate and save over WS (websockets==16.0)")
    args = parser.parse_args()
    client = Client(args.url)
    check_serving(client, args)
    if args.verify_state:
        state = json.loads(args.verify_state.read_text())
        require(state["mode"] == args.mode and state["version"] == args.version, "state mode/version mismatch")
        login(client, state)
    else:
        state = create(client, args)
    verify(client, state)
    if args.state:
        fd = os.open(args.state, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream)
    print("HTTP/SPA/auth/QSO/export smoke passed" + (" (saved state verified)" if args.verify_state else ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never print payloads, credentials, bearer tokens, or raw response bodies.
        print(f"Smoke failed: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
