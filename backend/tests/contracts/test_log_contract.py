"""OWNER/LOCATION/QSO/QUERY: doc/02, doc/03 分页, doc/04 三、四、五."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.location import Location
from app.models.qso_log import QSOLog


@pytest.mark.parametrize("length,expected", [(2, 422), (3, 201), (20, 201), (21, 422)])
def test_station_callsign_length_and_normalization(api_client, owner, length, expected):
    callsign = "b" * length
    response = api_client.post("/api/v1/stations", headers=owner.headers, json={"callsign": callsign})
    assert response.status_code == expected, response.text
    listed = api_client.get("/api/v1/stations", headers=owner.headers).json()
    if expected == 201:
        assert response.json()["callsign"] == callsign.upper()
        assert listed == [response.json()]
    else:
        assert listed == []


def test_station_callsign_whitespace_is_not_stored(api_client, owner):
    response = api_client.post("/api/v1/stations", headers=owner.headers, json={"callsign": "  ba7abc  "})
    assert response.status_code == 201, response.text
    assert response.json()["callsign"] == "BA7ABC"


def test_position_activation_is_per_user_and_spans_stations(api_client, owner, other, station_factory, location_factory):
    first_station = station_factory(owner, "BA1ONE")
    second_station = station_factory(owner, "BA1TWO")
    foreign_station = station_factory(other, "BA1OTH")
    first = location_factory(owner, first_station)
    second = location_factory(owner, second_station, name="Field", grid="OM88AA")
    foreign = location_factory(other, foreign_station, grid="PM95AA")
    assert first["is_active"] is True
    assert second["is_active"] is False
    assert foreign["is_active"] is True
    activation = api_client.post(f"/api/v1/locations/{second['id']}/activate", headers=owner.headers)
    assert activation.status_code == 200, activation.text
    assert activation.json()["is_active"] is True
    own_locations = api_client.get("/api/v1/locations", headers=owner.headers).json()
    assert {row["id"] for row in own_locations if row["is_active"]} == {second["id"]}
    assert {row["id"] for row in own_locations} == {first["id"], second["id"]}
    assert api_client.get("/api/v1/locations/active/current", headers=owner.headers).json()["id"] == second["id"]
    assert api_client.get("/api/v1/locations/active/current", headers=other.headers).json()["id"] == foreign["id"]
    assert {row["id"] for row in api_client.get("/api/v1/locations", headers=owner.headers,
                                                params={"station_id": first_station["id"]}).json()} == {first["id"]}


def test_minimal_qso_uses_active_location_and_utc(api_client, owner, station_factory, location_factory):
    stn = station_factory(owner)
    loc = location_factory(owner, stn)
    before = datetime.now(timezone.utc)
    response = api_client.post("/api/v1/logs", headers=owner.headers,
                               json={"call_sign": "  ja1abc  ", "band": "20m", "mode": "FT8", "freq": 14.074})
    after = datetime.now(timezone.utc)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["call_sign"] == "JA1ABC"
    assert body["user_id"] == owner.id
    assert body["station_id"] == stn["id"]
    assert body["location_id"] == loc["id"]
    assert body["my_gridsquare"] == "OM89AA"
    assert body["station_callsign"] == "BA1OWN"
    assert body["location_name"] == "Home"
    assert body["dxcc"] == "Japan"
    assert Decimal(str(body["freq"])) == Decimal("14.074")
    instant = datetime.fromisoformat(f"{body['qso_date']}T{body['time_on']}").replace(tzinfo=timezone.utc)
    assert before.replace(microsecond=0) <= instant <= after


def test_no_active_position_is_a_business_rejection(api_client, owner, db):
    response = api_client.get("/api/v1/locations/active/current", headers=owner.headers)
    assert response.status_code == 404, response.text
    response = api_client.post("/api/v1/logs", headers=owner.headers, json={"call_sign": "JA1ABC"})
    assert response.status_code == 422, response.text
    assert "active location" in response.json()["message"].lower()
    assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 0


def test_explicit_qso_datetime_location_and_grid_are_preserved(api_client, owner, station_factory, location_factory, log_factory):
    active_station = station_factory(owner, "BA1ACT")
    explicit_station = station_factory(owner, "BA1EXP")
    location_factory(owner, active_station)
    explicit_loc = location_factory(owner, explicit_station, grid="OM88AA")
    created = log_factory(owner, station_id=explicit_station["id"], location_id=explicit_loc["id"],
                          qso_date="2024-02-29", time_on="23:59:59", my_gridsquare="OL63AA")
    assert created["station_id"] == explicit_station["id"]
    assert created["location_id"] == explicit_loc["id"]
    assert created["qso_date"] == "2024-02-29"
    assert created["time_on"] == "23:59:59"
    assert created["my_gridsquare"] == "OL63AA"


@pytest.mark.parametrize("field,allowed", [
    ("qsl_sent", "YNRI"), ("qsl_rcvd", "YNRI"),
    ("eqsl_sent", "YNRI"), ("eqsl_rcvd", "YNRI"),
    ("lotw_sent", "YN"), ("lotw_rcvd", "YN"),
])
def test_confirmation_enumerations_and_invalid_patch_are_strict(api_client, owner, station_factory, log_factory, field, allowed):
    stn = station_factory(owner)
    created = log_factory(owner, station_id=stn["id"])
    url = f"/api/v1/logs/{created['id']}"
    for value in allowed:
        response = api_client.patch(url, headers=owner.headers, json={field: value})
        assert response.status_code == 200, response.text
        assert response.json()[field] == value
    response = api_client.patch(url, headers=owner.headers, json={field: "X"})
    assert response.status_code == 422, response.text
    assert api_client.get(url, headers=owner.headers).json()[field] == allowed[-1]


def test_creation_qsl_linkage_does_not_run_on_patch(api_client, owner, station_factory, log_factory):
    stn = station_factory(owner)
    confirmed = log_factory(owner, station_id=stn["id"], qsl_rcvd="Y")
    fields = ("qsl_sent", "qsl_rcvd", "lotw_sent", "lotw_rcvd", "eqsl_sent", "eqsl_rcvd")
    assert {key: confirmed[key] for key in fields} == dict.fromkeys(fields, "Y")
    ordinary = log_factory(owner, station_id=stn["id"], call_sign="JA2ABC")
    response = api_client.patch(f"/api/v1/logs/{ordinary['id']}", headers=owner.headers, json={"qsl_rcvd": "Y"})
    assert response.status_code == 200, response.text
    expected = dict.fromkeys(fields, "N")
    expected["qsl_rcvd"] = "Y"
    assert {key: response.json()[key] for key in fields} == expected


@pytest.mark.parametrize("reference", ["foreign_station", "foreign_location", "deleted_station", "deleted_location", "mismatch"])
def test_invalid_qso_references_reject_without_writes(api_client, db, owner, other, station_factory, location_factory, reference):
    own_stn = station_factory(owner)
    own_loc = location_factory(owner, own_stn)
    foreign_stn = station_factory(other, "BA1OTH")
    foreign_loc = location_factory(other, foreign_stn)
    payload = {"call_sign": "JA1ABC", "station_id": own_stn["id"], "location_id": own_loc["id"]}
    expected = 404
    if reference == "foreign_station":
        payload.update(station_id=foreign_stn["id"], location_id=None)
    elif reference == "foreign_location":
        payload["location_id"] = foreign_loc["id"]
    elif reference == "deleted_station":
        assert api_client.delete(f"/api/v1/stations/{own_stn['id']}", headers=owner.headers).status_code == 204
    elif reference == "deleted_location":
        assert api_client.delete(f"/api/v1/locations/{own_loc['id']}", headers=owner.headers).status_code == 204
    else:
        own_second = station_factory(owner, "BA1TWO")
        payload["station_id"] = own_second["id"]
        expected = 422
    before = db.query(QSOLog).count()
    response = api_client.post("/api/v1/logs", headers=owner.headers, json=payload)
    assert response.status_code == expected, response.text
    assert db.query(QSOLog).count() == before


def test_patch_must_keep_owned_consistent_references(api_client, owner, other, station_factory, location_factory, log_factory):
    first = station_factory(owner)
    first_loc = location_factory(owner, first)
    second = station_factory(owner, "BA1TWO")
    second_loc = location_factory(owner, second, grid="OL63AA")
    foreign = station_factory(other, "BA1OTH")
    foreign_loc = location_factory(other, foreign)
    qso = log_factory(owner, station_id=first["id"], location_id=first_loc["id"])
    url = f"/api/v1/logs/{qso['id']}"
    for payload, expected in [({"location_id": foreign_loc["id"]}, 404),
                              ({"station_id": foreign["id"]}, 404),
                              ({"location_id": second_loc["id"]}, 422)]:
        response = api_client.patch(url, headers=owner.headers, json=payload)
        assert response.status_code == expected, response.text
        current = api_client.get(url, headers=owner.headers).json()
        assert (current["station_id"], current["location_id"]) == (first["id"], first_loc["id"])
    response = api_client.patch(url, headers=owner.headers,
                                json={"station_id": second["id"], "location_id": second_loc["id"]})
    assert response.status_code == 200, response.text
    assert (response.json()["station_id"], response.json()["location_id"]) == (second["id"], second_loc["id"])


def test_foreign_qso_cannot_be_read_mutated_or_deleted(api_client, owner, other, station_factory, log_factory):
    stn = station_factory(owner)
    qso = log_factory(owner, station_id=stn["id"], comment="private")
    url = f"/api/v1/logs/{qso['id']}"
    assert api_client.get(url, headers=other.headers).status_code == 404
    assert api_client.patch(url, headers=other.headers, json={"comment": "hijacked"}).status_code == 404
    assert api_client.delete(url, headers=other.headers).status_code == 404
    assert api_client.get(url, headers=owner.headers).json()["comment"] == "private"
    assert api_client.get("/api/v1/logs", headers=other.headers).json()["items"] == []


def test_position_soft_delete_keeps_existing_qso_reference(api_client, db, owner, station_factory, location_factory, log_factory):
    stn = station_factory(owner)
    loc = location_factory(owner, stn)
    qso = log_factory(owner, station_id=stn["id"], location_id=loc["id"])
    response = api_client.delete(f"/api/v1/locations/{loc['id']}", headers=owner.headers)
    assert response.status_code == 204 and response.content == b""
    db.expire_all()
    assert db.get(Location, loc["id"]).is_deleted is True
    assert db.get(QSOLog, qso["id"]).location_id == loc["id"]
    assert api_client.get(f"/api/v1/logs/{qso['id']}", headers=owner.headers).status_code == 200


@pytest.fixture
def query_dataset(owner, other, station_factory, log_factory, api_client):
    first = station_factory(owner, "BA1ONE")
    second = station_factory(owner, "BA1TWO")
    foreign = station_factory(other, "BA1OTH")
    values = [
        ("JA1AAA", "2026-01-01", "20m", "FT8", "PM95AA", "Japan", first),
        ("JA2BBB", "2026-01-02", "40m", "CW", "PM96AA", "Japan", second),
        ("K1CCC", "2026-01-03", "20m", "SSB", "FN31AA", "United States", first),
        ("JA3DDD", "2026-01-04", "20m", "FT8", "PM95BB", "Japan", second),
    ]
    records = {}
    for call, day, band, mode, grid, entity, stn in values:
        records[call] = log_factory(owner, station_id=stn["id"], call_sign=call, qso_date=day,
                                   band=band, mode=mode, grid_square=grid, dxcc=entity)
    log_factory(other, station_id=foreign["id"], call_sign="JA9HID", qso_date="2026-01-05")
    deleted = log_factory(owner, station_id=first["id"], call_sign="JA8DEL", qso_date="2026-01-06")
    assert api_client.delete(f"/api/v1/logs/{deleted['id']}", headers=owner.headers).status_code == 204
    return first, second, records


@pytest.mark.parametrize("params,expected", [
    ({}, ["JA3DDD", "K1CCC", "JA2BBB", "JA1AAA"]),
    ({"start_date": "2026-01-02", "end_date": "2026-01-03"}, ["K1CCC", "JA2BBB"]),
    ({"call_sign": "A2B"}, ["JA2BBB"]),
    ({"grid_square": "pm95"}, ["JA3DDD", "JA1AAA"]),
    ({"band": "20m", "mode": "FT8", "dxcc": "Japan"}, ["JA3DDD", "JA1AAA"]),
    ({"sort_by": "unrecognized", "sort_order": "asc"}, ["JA1AAA", "JA2BBB", "K1CCC", "JA3DDD"]),
    ({"sort_by": "call_sign", "sort_order": "asc"}, ["JA1AAA", "JA2BBB", "JA3DDD", "K1CCC"]),
])
def test_log_filters_and_sorting_exact_result_sets(api_client, owner, query_dataset, params, expected):
    response = api_client.get("/api/v1/logs", headers=owner.headers, params=params)
    assert response.status_code == 200, response.text
    body = response.json()
    assert [row["call_sign"] for row in body["items"]] == expected
    assert body["total"] == len(expected)
    assert body["pages"] == 1


def test_log_pagination_total_pages_and_station_scope(api_client, owner, query_dataset):
    first, _, _ = query_dataset
    response = api_client.get("/api/v1/logs", headers=owner.headers, params={"page": 2, "page_size": 2})
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["page"], body["page_size"], body["total"], body["pages"]) == (2, 2, 4, 2)
    assert [row["call_sign"] for row in body["items"]] == ["JA2BBB", "JA1AAA"]
    station = api_client.get("/api/v1/logs", headers=owner.headers, params={"station_id": first["id"]}).json()
    assert {row["call_sign"] for row in station["items"]} == {"JA1AAA", "K1CCC"}
    assert station["total"] == 2


@pytest.mark.parametrize("params,expected", [
    ({"page": 0}, 422), ({"page": 1}, 200), ({"page_size": 0}, 422),
    ({"page_size": 1}, 200), ({"page_size": 100}, 200), ({"page_size": 101}, 422),
    ({"sort_order": "sideways"}, 422), ({"sort_by": "qso_date;drop"}, 422),
    ({"start_date": "2026-02-30"}, 422),
])
def test_query_parameter_boundaries(api_client, owner, params, expected):
    response = api_client.get("/api/v1/logs", headers=owner.headers, params=params)
    assert response.status_code == expected, response.text
    if expected == 200:
        assert response.json()["items"] == []
        assert response.json()["total"] == 0
        assert response.json()["pages"] == 0
