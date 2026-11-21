"""IMPORT/EXPORT: doc/12 matrix; doc/04 §五; doc/02 transaction rules."""
import re
from decimal import Decimal

import pytest
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.models.log_file import LogFile
from app.models.qso_log import QSOLog

ROOT = "/api/v1/logs"


def adi(**changes):
    values = {"call": "JA1ABC", "qso_date": "20260102", "time_on": "123456",
              "band": "20m", "mode": "FT8", "freq": "14.074", **changes}
    return " ".join(f"<{key}:{len(str(value))}>{value}" for key, value in values.items()) + " <EOR>\n"


def upload(client, operator, content, station=None, filename="contacts.adi", **kwargs):
    return client.post(ROOT + "/import", headers=operator.headers,
                       params={} if station is None else {"station_id": station["id"]},
                       files={"file": (filename, content, "application/octet-stream")}, **kwargs)


def records(response):
    """Independent length-delimited ADIF reader, never the application parser."""
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/octet-stream")
    assert re.search(r'attachment; filename="\d{8}_.+\.adi"', response.headers["content-disposition"])
    text = response.text
    position = 0
    current, result = {}, []
    while position < len(text):
        match = re.search(r"<([^>]+)>", text[position:])
        if not match:
            assert not text[position:].strip()
            break
        position += match.end()
        tag = match.group(1).upper()
        if tag == "EOH":
            current = {}
        elif tag == "EOR":
            result.append(current)
            current = {}
        else:
            parts = tag.split(":")
            assert len(parts) in (2, 3) and parts[1].isdigit(), tag
            length = int(parts[1])
            assert position + length <= len(text)
            assert parts[0] not in current
            current[parts[0]] = text[position:position + length]
            position += length
    assert not current
    return result


@pytest.mark.parametrize("suffix", ["adi", "ADI", "adif", "ADIF"])
def test_filename_case_and_explicit_station(api_client, owner, station_factory, suffix):
    """04 §五 import: multipart file accepts both suffixes in either case."""
    station = station_factory(owner)
    response = upload(api_client, owner, adi(), station, "contacts." + suffix)
    assert response.status_code == 200, response.text
    body = response.json()
    assert {key: body[key] for key in ("total_records", "imported", "duplicates", "merged", "updated", "skipped")} == {
        "total_records": 1, "imported": 1, "duplicates": 0, "merged": 0, "updated": 0, "skipped": 0}
    assert body["status"] == "success" and body["database_failed"] is False
    assert body["errors"] == [] and isinstance(body["file_id"], int)
    rows = api_client.get(ROOT, headers=owner.headers).json()["items"]
    assert len(rows) == 1 and rows[0]["station_id"] == station["id"]


@pytest.mark.parametrize("limit", [512, 50 * 1024 * 1024])
def test_exact_byte_limit_and_one_over(api_client, owner, station_factory, monkeypatch, db, limit):
    """04 §五 import: configured and actual 50 MiB payload boundary, excluding multipart overhead."""
    station = station_factory(owner)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", limit)
    record = adi().encode()
    payload = record + b" " * (limit - len(record))
    accepted = upload(api_client, owner, payload, station)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["imported"] == 1
    rejected = upload(api_client, owner, payload + b" ", station)
    assert rejected.status_code == 413, rejected.text
    db.expire_all()
    assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 1
    assert db.query(LogFile).filter_by(user_id=owner.id).count() == 1


def test_multipart_query_and_missing_active_location(api_client, owner, station_factory, db):
    """04 §五: station_id is a query parameter, not multipart fallback; no active location is 400."""
    station = station_factory(owner)
    response = upload(api_client, owner, adi())
    assert response.status_code == 400, response.text
    response = upload(api_client, owner, adi(), data={"station_id": str(station["id"])})
    assert response.status_code == 400, response.text
    response = api_client.post(ROOT + "/import", headers=owner.headers,
                               params={"station_id": station["id"]}, json={"file": adi()})
    assert response.status_code == 422, response.text
    response = upload(api_client, owner, adi(), station, "contacts.txt")
    assert response.status_code == 400, response.text
    assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 0
    assert db.query(LogFile).filter_by(user_id=owner.id).count() == 0


def test_default_station_uses_active_location(api_client, owner, station_factory, location_factory):
    """04 §五 import: absent station chooses the activated location's owned station."""
    first = station_factory(owner)
    station_factory(owner, "BA2OWN")
    location = location_factory(owner, first)
    response = upload(api_client, owner, adi())
    assert response.status_code == 200, response.text
    rows = api_client.get(ROOT, headers=owner.headers).json()["items"]
    assert len(rows) == 1
    assert (rows[0]["station_id"], rows[0]["location_id"]) == (first["id"], location["id"])


@pytest.mark.parametrize("deleted", [False, True])
def test_import_rejects_foreign_or_deleted_station(api_client, owner, other, station_factory, db, deleted):
    """02 ownership/lifecycle; 04 §五: inaccessible import parents return 404 without writes."""
    station = station_factory(owner if deleted else other)
    if deleted:
        response = api_client.delete(f"/api/v1/stations/{station['id']}", headers=owner.headers)
        assert response.status_code == 204, response.text
    response = upload(api_client, owner, adi(), station)
    assert response.status_code == 404, response.text
    assert db.query(QSOLog).count() == 0
    assert db.query(LogFile).count() == 0


@pytest.mark.parametrize("key,value", [("call", "JA2ABC"), ("qso_date", "20260103"),
    ("time_on", "123457"), ("band", "40m"), ("mode", "SSB"), ("freq", "14.075")])
def test_each_dedup_key_component_is_significant(api_client, owner, station_factory, key, value):
    """04 §五 import: changing each of six identity fields independently creates a QSO."""
    station = station_factory(owner)
    response = upload(api_client, owner, adi() + adi(**{key: value}), station)
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 2
    assert response.json()["duplicates"] == 0
    assert api_client.get(ROOT, headers=owner.headers).json()["total"] == 2


def test_dedup_cross_station_not_cross_user_or_deleted(api_client, owner, other, station_factory, log_factory):
    """04 §五 import: user's live records span stations, but not other users or deleted QSOs."""
    first = station_factory(owner)
    second = station_factory(owner, "BA2OWN")
    foreign = station_factory(other, "BA3OTH")
    existing = log_factory(owner, station_id=first["id"])
    assert upload(api_client, other, adi(), foreign).json()["imported"] == 1
    response = upload(api_client, owner, adi(), second)
    assert response.status_code == 200, response.text
    assert response.json()["duplicates"] == 1 and response.json()["imported"] == 0
    assert api_client.get(f"{ROOT}/{existing['id']}", headers=owner.headers).json()["station_id"] == first["id"]
    assert api_client.delete(f"{ROOT}/{existing['id']}", headers=owner.headers).status_code == 204
    response = upload(api_client, owner, adi(), second)
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 1


def test_merge_fills_only_empty_and_never_downgrades_confirmations(api_client, owner, station_factory, log_factory):
    """04 §五 import: fill-only merge and all three confirmation channels are monotonic."""
    station = station_factory(owner)
    original = log_factory(owner, station_id=station["id"], rst_sent="599", comment="keep", tx_pwr=5,
                           my_gridsquare="OM89AA", qso_date_off="2026-01-02", time_off="12:35:00")
    response = upload(api_client, owner, adi(rst_sent="579", rst_rcvd="589", gridsquare="PM95AA",
        my_gridsquare="PM96AA", comment="replace", tx_pwr="100", qso_date_off="20260103", time_off="140000",
        qsl_rcvd="Y", lotw_rcvd="Y", eqsl_rcvd="Y"), station)
    assert response.status_code == 200, response.text
    assert response.json()["merged"] == response.json()["updated"] == 1
    row = api_client.get(f"{ROOT}/{original['id']}", headers=owner.headers).json()
    for field, expected in {"rst_sent": "599", "rst_rcvd": "589", "grid_square": "PM95AA",
        "comment": "keep", "tx_pwr": 5, "my_gridsquare": "OM89AA", "qso_date_off": "2026-01-02",
        "time_off": "12:35:00"}.items():
        assert row[field] == expected
    for field in ("qsl_sent", "qsl_rcvd", "lotw_sent", "lotw_rcvd", "eqsl_sent", "eqsl_rcvd"):
        assert row[field] == "Y"
    response = upload(api_client, owner, adi(qsl_rcvd="N", lotw_rcvd="N", eqsl_rcvd="N"), station)
    assert response.status_code == 200, response.text
    assert response.json()["duplicates"] == 1 and response.json()["merged"] == 0
    after = api_client.get(f"{ROOT}/{original['id']}", headers=owner.headers).json()
    for field in ("qsl_sent", "qsl_rcvd", "lotw_sent", "lotw_rcvd", "eqsl_sent", "eqsl_rcvd"):
        assert after[field] == "Y"


def test_invalid_record_counts_and_ten_error_cap(api_client, owner, station_factory):
    """04 §五 import: eleven invalid records preserve record ordinals while errors cap at ten."""
    station = station_factory(owner)
    response = upload(api_client, owner, adi() + "".join(adi(call=f"JA{i}BAD", freq="not-a-number") for i in range(11)), station)
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["total_records"], body["imported"], body["skipped"], body["duplicates"], body["merged"]) == (12, 1, 11, 0, 0)
    assert body["status"] == "partial" and body["database_failed"] is False
    assert len(body["errors"]) == 10
    assert [error["line"] for error in body["errors"]] == list(range(2, 12))
    assert all(isinstance(error["error"], str) and error["error"] for error in body["errors"])


@pytest.mark.parametrize("size", [499, 500, 501])
@pytest.mark.parametrize("fail", [False, True])
def test_batch_edges_report_only_persisted_http_counts(api_client, owner, station_factory, db, size, fail):
    """02 transactions; 04 §五 import: HTTP 503 reports committed batches, including exact 500 edge."""
    station = station_factory(owner)
    engine = db.get_bind()
    writes = 0

    def fault(connection, cursor, statement, parameters, context, executemany):
        nonlocal writes
        if statement.lstrip().upper().startswith("INSERT INTO QSO_LOGS"):
            writes += 1
            if fail and writes == (501 if size == 501 else size):
                raise OperationalError(statement, parameters, RuntimeError("contract transaction fault"))

    event.listen(engine, "before_cursor_execute", fault)
    try:
        response = upload(api_client, owner, "".join(adi(call=f"JA{i:05d}") for i in range(size)), station)
    finally:
        event.remove(engine, "before_cursor_execute", fault)
    assert response.status_code == (503 if fail else 200), response.text
    body = response.json()
    expected = (500 if size == 501 else 0) if fail else size
    assert body["imported"] == expected
    assert body["total_records"] == size
    assert body["duplicates"] == body["merged"] == body["updated"] == body["skipped"] == 0
    assert body["database_failed"] is fail
    assert body["status"] == (("partial" if expected else "failed") if fail else "success")
    db.expire_all()
    assert db.query(QSOLog).filter_by(user_id=owner.id, is_deleted=False).count() == expected
    metadata = db.get(LogFile, body["file_id"])
    assert metadata.qso_count == expected and metadata.import_status == body["status"]
    if fail:
        assert body["errors"] and "rolled back" in body["errors"][0]["error"]
    else:
        assert body["errors"] == []


@pytest.mark.parametrize("format", ["adi", "adif"])
def test_export_fields_and_independent_adif_decoding(api_client, owner, station_factory, log_factory, format):
    """04 §五 export; 02 QSO units: six independent QSL states, MHz and extended fields."""
    station = station_factory(owner)
    row = log_factory(owner, station_id=station["id"], freq_rx=14.076, band_rx="20m", rst_sent="579",
        rst_rcvd="589", grid_square="PM95AA", my_gridsquare="OM89AA", my_call="BA9OP", tx_pwr=25,
        prop_mode="SAT", sat_name="TEST-SAT", srx="007", stx="008", contest_id="TEST", comment="literal <EOR> note",
        qso_date_off="2026-01-03", time_off="00:01:02")
    flags = {"qsl_sent": "R", "qsl_rcvd": "I", "lotw_sent": "Y", "lotw_rcvd": "N", "eqsl_sent": "I", "eqsl_rcvd": "R"}
    patched = api_client.patch(f"{ROOT}/{row['id']}", headers=owner.headers, json=flags)
    assert patched.status_code == 200, patched.text
    exported = records(api_client.get(ROOT + "/export", headers=owner.headers, params={"format": format}))
    assert len(exported) == 1
    actual = exported[0]
    expected = {"CALL": "JA1ABC", "QSO_DATE": "20260102", "TIME_ON": "123456", "QSO_DATE_OFF": "20260103",
        "TIME_OFF": "000102", "BAND": "20m", "BAND_RX": "20m", "MODE": "FT8", "RST_SENT": "579",
        "RST_RCVD": "589", "GRIDSQUARE": "PM95AA", "MY_GRIDSQUARE": "OM89AA", "MY_CALL": "BA9OP",
        "STATION_CALLSIGN": station["callsign"], "TX_PWR": "25", "PROP_MODE": "SAT", "SAT_NAME": "TEST-SAT",
        "SRX": "007", "STX": "008", "CONTEST_ID": "TEST", "COMMENT": "literal <EOR> note",
        **{key.upper(): value for key, value in flags.items()}}
    for key, value in expected.items():
        assert actual[key] == value
    assert Decimal(actual["FREQ"]) == Decimal("14.074")
    assert Decimal(actual["FREQ_RX"]) == Decimal("14.076")


def test_export_filters_my_grid_prefix_not_location_id(api_client, owner, other, station_factory, location_factory, log_factory):
    """04 §五 export: intersection of date/band/station and location's first-four my_grid semantics."""
    station = station_factory(owner)
    second = station_factory(owner, "BA2OWN")
    loc = location_factory(owner, station, grid="OM89AA")
    elsewhere = location_factory(owner, station, name="Elsewhere", grid="PM95AA")
    def make(call, **fields):
        return log_factory(owner, call_sign=call, station_id=station["id"], location_id=elsewhere["id"],
                           my_gridsquare="OM89BB", **fields)
    make("JA1YES")
    log_factory(owner, call_sign="JA2NO", station_id=station["id"], location_id=loc["id"], my_gridsquare="PM95AA")
    make("JA3DATE", qso_date="2026-01-01")
    make("JA4BAND", band="40m")
    log_factory(owner, call_sign="JA5STN", station_id=second["id"], my_gridsquare="OM89CC")
    gone = make("JA6GONE")
    assert api_client.delete(f"{ROOT}/{gone['id']}", headers=owner.headers).status_code == 204
    foreign = station_factory(other, "BA3OTH")
    log_factory(other, call_sign="JA7OTHER", station_id=foreign["id"], my_gridsquare="OM89AA")
    response = api_client.get(ROOT + "/export", headers=owner.headers, params={"station_id": station["id"],
        "location_id": loc["id"], "start_date": "2026-01-02", "end_date": "2026-01-02", "band": "20m"})
    assert [row["CALL"] for row in records(response)] == ["JA1YES"]
    assert "_OM89.adi" in response.headers["content-disposition"]


@pytest.mark.parametrize("parent", ["station", "location"])
@pytest.mark.parametrize("deleted", [False, True])
def test_export_rejects_inaccessible_parents(api_client, owner, other, station_factory, location_factory, parent, deleted):
    """02 ownership and 04 §五 export: foreign/deleted filter parents cannot expose a file."""
    operator = owner if deleted else other
    station = station_factory(operator)
    location = location_factory(operator, station)
    selected = station if parent == "station" else location
    if deleted:
        path = "stations" if parent == "station" else "locations"
        response = api_client.delete(f"/api/v1/{path}/{selected['id']}", headers=operator.headers)
        assert response.status_code == 204, response.text
    response = api_client.get(ROOT + "/export", headers=owner.headers, params={parent + "_id": selected["id"]})
    assert response.status_code == 404, response.text
