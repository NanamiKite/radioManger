"""Specification-driven public realtime contracts; MySQL mode is logic-only SQLite."""
import json
import socket
import threading
import time
from contextlib import contextmanager
from decimal import Decimal

import anyio
import pytest

from sqlalchemy import event, text
from app.config import settings


WS_PATHS = ("/api/v1/udp/ws", "/api/v1/dxcluster/ws")


def receive_frame(ws, timeout=2):
    """Bound the actual TestClient transport receive, including a missing close frame."""
    async def receive():
        with anyio.fail_after(timeout):
            return await ws._send_rx.receive()
    return ws.portal.call(receive)


def receive_json(ws, timeout=2):
    frame = receive_frame(ws, timeout)
    assert frame["type"] == "websocket.send", frame
    return json.loads(frame["text"])


def assert_closed(ws, timeout=2):
    frame = receive_frame(ws, timeout)
    assert frame["type"] == "websocket.close", frame
    assert frame["code"] == 4401, frame


@contextmanager
def udp_ports():
    sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(2)]
    try:
        for sock in sockets:
            sock.bind(("127.0.0.1", 0))
        ports = [sock.getsockname()[1] for sock in sockets]
        for sock in sockets:
            sock.close()
        yield {"wsjtx_port": ports[0], "n1mm_port": ports[1]}
    finally:
        for sock in sockets:
            sock.close()


@pytest.fixture(autouse=True)
def loopback_configuration(monkeypatch):
    monkeypatch.setattr(settings, "UDP_BIND_HOST", "127.0.0.1")
    monkeypatch.setattr(settings, "UDP_ALLOWED_SOURCES", ["127.0.0.1"])
    monkeypatch.setattr(settings, "DX_CLUSTER_NODES", [])


@pytest.mark.parametrize("api_mode", ["mysql"], indirect=True)
@pytest.mark.parametrize("path,payload", [
    ("/api/v1/dxcluster/connect", {"node_host": "127.0.0.1", "node_port": 7300}),
    ("/api/v1/dxcluster/disconnect", None),
    ("/api/v1/udp/start", {"wsjtx_port": 2237, "n1mm_port": 12060}),
    ("/api/v1/udp/stop", None),
])
def test_mysql_logic_ordinary_user_host_control_is_403(api_client, owner, path, payload):
    response = api_client.post(path, headers=owner.headers, json=payload)
    assert response.status_code == 403, response.text
    assert api_client.get("/api/v1/udp/status", headers=owner.headers).json()["data"]["running"] is False
    assert api_client.get("/api/v1/dxcluster/status", headers=owner.headers).json()["connected"] is False


@pytest.mark.parametrize("api_mode", ["mysql"], indirect=True)
def test_admin_connects_only_configured_loopback_node(api_client, operator_factory,
                                                      station_factory, location_factory, monkeypatch):
    admin = operator_factory("contract_admin", role="admin")
    station = station_factory(admin, callsign="BA1ADM")
    location_factory(admin, station)
    with socket.socket() as server, socket.socket() as forbidden:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.settimeout(3)
        forbidden.bind(("127.0.0.1", 0))
        forbidden.listen(1)
        forbidden.settimeout(0.2)
        port = server.getsockname()[1]
        monkeypatch.setattr(settings, "DX_CLUSTER_NODES", [f"127.0.0.1:{port}"])
        callsigns = []
        errors = []
        def node():
            try:
                connection, _ = server.accept()
                with connection:
                    connection.settimeout(3)
                    connection.sendall(b"login:\n")
                    stream = connection.makefile("rb")
                    callsigns.append(stream.readline().strip())
                    assert stream.readline() == b""
                    stream.close()
            except BaseException as exc:
                errors.append(exc)
        worker = threading.Thread(target=node, daemon=True)
        worker.start()
        response = api_client.post("/api/v1/dxcluster/connect", headers=admin.headers,
                                   json={"node_host": "127.0.0.1", "node_port": port})
        try:
            assert response.status_code == 200, response.text
            assert response.json()["success"] is True
            assert response.json()["status"]["connected"] is True
            rejected = api_client.post("/api/v1/dxcluster/connect", headers=admin.headers,
                                      json={"node_host": "127.0.0.1", "node_port": forbidden.getsockname()[1]})
            assert rejected.status_code == 422, rejected.text
            with pytest.raises(socket.timeout):
                forbidden.accept()
            state = api_client.get("/api/v1/dxcluster/status", headers=admin.headers).json()
            assert state["current_node"]["port"] == port
            assert state["connected"] is True
        finally:
            stopped = api_client.post("/api/v1/dxcluster/disconnect", headers=admin.headers)
            worker.join(4)
        assert stopped.status_code == 200, stopped.text
        assert stopped.json()["connected"] is False
        assert not worker.is_alive()
        assert not errors, errors
        assert callsigns == [b"BA1ADM"]
        with udp_ports() as ports:
            started = api_client.post("/api/v1/udp/start", headers=admin.headers, json=ports)
            assert started.status_code == 200, started.text
            assert started.json()["data"]["receiving"] is True
            stopped = api_client.post("/api/v1/udp/stop", headers=admin.headers)
            assert stopped.status_code == 200, stopped.text
            assert stopped.json() == {"data": {"running": False}}


@pytest.mark.parametrize("payload", [
    {"wsjtx_port": 1023, "n1mm_port": 12060},
    {"wsjtx_port": 65536, "n1mm_port": 12060},
    {"wsjtx_port": 2237, "n1mm_port": 1023},
    {"wsjtx_port": 2237, "n1mm_port": 65536},
    {"wsjtx_port": 12060, "n1mm_port": 12060},
])
def test_invalid_udp_ports_are_422_without_starting(api_client, owner, payload):
    response = api_client.post("/api/v1/udp/start", headers=owner.headers, json=payload)
    assert response.status_code == 422, response.text
    state = api_client.get("/api/v1/udp/status", headers=owner.headers).json()["data"]
    assert state["running"] is False
    assert state["receiving"] is False
    assert state["qso_count"] == 0


@pytest.mark.parametrize("occupied_key", ["wsjtx_port", "n1mm_port"])
def test_real_udp_bind_conflict_is_409_and_releases_partial_socket(api_client, owner, occupied_key):
    with udp_ports() as ports, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as occupied:
        occupied.bind(("127.0.0.1", ports[occupied_key]))
        response = api_client.post("/api/v1/udp/start", headers=owner.headers, json=ports)
        assert response.status_code == 409, response.text
        state = api_client.get("/api/v1/udp/status", headers=owner.headers).json()["data"]
        assert state["running"] is False
        assert state["receiving"] is False
        assert state["last_qso"] is None
        free_key = "n1mm_port" if occupied_key == "wsjtx_port" else "wsjtx_port"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(("127.0.0.1", ports[free_key]))
        occupied.close()
        response = api_client.post("/api/v1/udp/start", headers=owner.headers, json=ports)
        assert response.status_code == 200, response.text
        assert response.json()["data"]["running"] is True
        assert api_client.post("/api/v1/udp/stop", headers=owner.headers).status_code == 200


@pytest.mark.parametrize("path", WS_PATHS)
@pytest.mark.parametrize("query_token", [False, True])
def test_ws_requires_first_message_within_five_seconds(api_client, owner, path, query_token):
    url = path + (f"?token={owner.token}" if query_token else "")
    with api_client.websocket_connect(url) as ws:
        started = time.monotonic()
        assert_closed(ws, timeout=6.5)
        elapsed = time.monotonic() - started
        assert 4.5 <= elapsed <= 6.5, elapsed


@pytest.mark.parametrize("path", WS_PATHS)
@pytest.mark.parametrize("message", [{"token": "invalid.jwt.token"}, {}, {"token": ""}, []])
def test_ws_invalid_first_message_closes_4401(api_client, path, message):
    with api_client.websocket_connect(path) as ws:
        ws.send_json(message)
        assert_closed(ws)


@pytest.mark.parametrize("path", WS_PATHS)
def test_ws_idle_revocation_closes_within_ten_seconds_and_returns_connections(api_client, owner, db, path):
    engine = db.get_bind()
    db.rollback()
    authenticated = threading.Event()
    leases = []
    def checkout(*args):
        leases.append(1)
    def checkin(*args):
        leases.pop()
        authenticated.set()
    event.listen(engine, "checkout", checkout)
    event.listen(engine, "checkin", checkin)
    try:
        with api_client.websocket_connect(path) as ws:
            # Accept a valid first message near, but inside, the five-second window.
            time.sleep(4)
            ws.send_json({"token": owner.token})
            assert authenticated.wait(2), "WebSocket authentication did not release its DB connection"
            assert leases == [], "Idle WebSocket must not retain a DB checkout"
            revoked = api_client.post("/api/v1/auth/logout", headers=owner.headers)
            assert revoked.status_code == 200, revoked.text
            started = time.monotonic()
            assert_closed(ws, timeout=11.5)
            assert time.monotonic() - started <= 11.5
        assert leases == [], "Revoked authentication leaked a DB connection"
        with api_client.websocket_connect(path) as rejected:
            rejected.send_json({"token": owner.token})
            assert_closed(rejected)
        assert leases == [], "Failed authentication leaked a DB connection"
    finally:
        event.remove(engine, "checkout", checkout)
        event.remove(engine, "checkin", checkin)


def test_ws_save_revalidates_before_periodic_deadline(api_client, owner, station_factory, location_factory, db):
    location_factory(owner, station_factory(owner))
    with api_client.websocket_connect("/api/v1/udp/ws") as ws:
        ws.send_json({"token": owner.token})
        ws.send_json({"action": "invalid"})
        assert receive_json(ws)["type"] == "error"
        response = api_client.post("/api/v1/auth/logout", headers=owner.headers)
        assert response.status_code == 200, response.text
        ws.send_json({"action": "save", "data": {
            "call_sign": "JA1ABC", "qso_date": "2026-01-02", "time_on": "12:34:56",
            "band": "20m", "mode": "FT8"}})
        assert_closed(ws, timeout=2)
    assert db.execute(text("SELECT count(*) FROM qso_logs")).scalar_one() == 0


def test_udp_raw_broadcast_is_owner_only_redacted_and_not_automatically_saved(
        api_client, owner, other, station_factory, location_factory):
    location_factory(owner, station_factory(owner))
    with udp_ports() as ports:
        started = api_client.post("/api/v1/udp/start", headers=owner.headers, json=ports)
        assert started.status_code == 200, started.text
        with api_client.websocket_connect("/api/v1/udp/ws") as own_ws, \
                api_client.websocket_connect("/api/v1/udp/ws") as other_ws:
            for ws, operator in ((own_ws, owner), (other_ws, other)):
                ws.send_json({"token": operator.token})
                ws.send_json({"action": "invalid"})
                assert receive_json(ws)["type"] == "error"
            packet = (b"<contactinfo><call>JA1ABC</call><timestamp>2026-01-02 12:34:56</timestamp>"
                      b"<rxfreq>1407400</rxfreq><mode>FT8</mode><snt>-10</snt><rcv>-12</rcv>"
                      b"<gridsquare>PM95AA</gridsquare></contactinfo>")
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                sender.sendto(packet, ("127.0.0.1", ports["n1mm_port"]))
            message = receive_json(own_ws)
            assert message["type"] == "qso_received"
            assert message["source"] == "n1mm"
            assert message["count"] == 1
            assert {key: message["data"][key] for key in
                    ("call_sign", "qso_date", "time_on", "mode", "grid_square")} == {
                "call_sign": "JA1ABC", "qso_date": "2026-01-02", "time_on": "12:34:56",
                "mode": "FT8", "grid_square": "PM95AA"}
            assert Decimal(str(message["data"]["freq"])) == Decimal("14.074")
            # A subsequent error is a FIFO barrier: any leaked broadcast would arrive first.
            other_ws.send_json({"action": "invalid"})
            assert receive_json(other_ws)["type"] == "error"
            own_state = api_client.get("/api/v1/udp/status", headers=owner.headers).json()["data"]
            other_state = api_client.get("/api/v1/udp/status", headers=other.headers).json()["data"]
            assert own_state["qso_count"] == 1
            assert own_state["last_qso"]["call_sign"] == "JA1ABC"
            assert other_state["running"] is True
            assert other_state["receiving"] is False
            assert other_state["qso_count"] == 0
            assert other_state["last_qso"] is None
            for path, payload in (("/api/v1/udp/stop", None), ("/api/v1/udp/start", ports)):
                rejected = api_client.post(path, headers=other.headers, json=payload)
                assert rejected.status_code == 403, rejected.text
            for operator in (owner, other):
                logs = api_client.get("/api/v1/logs", headers=operator.headers)
                assert logs.status_code == 200, logs.text
                assert logs.json()["total"] == 0
            own_ws.send_json({"action": "save", "data": message["data"]})
            saved = receive_json(own_ws)
            assert saved["type"] == "qso_saved"
            assert saved["data"]["call_sign"] == "JA1ABC"
            logs = api_client.get("/api/v1/logs", headers=owner.headers).json()
            assert logs["total"] == 1
            assert logs["items"][0]["id"] == saved["data"]["id"]
        stopped = api_client.post("/api/v1/udp/stop", headers=owner.headers)
        assert stopped.status_code == 200, stopped.text
        assert stopped.json() == {"data": {"running": False}}
