"""RECYCLE: doc/12 matrix, doc/04 §五 recycle, doc/02 lifecycle and cascade."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.deleted_log import DeletedLog
from app.models.location import Location
from app.models.qso_log import QSOLog
from app.models.station import Station

ROOT = "/api/v1/logs"


def listing(client, operator):
    response = client.get(ROOT + "/recycle/list", headers=operator.headers)
    assert response.status_code == 200, response.text
    return response.json()


def delete(client, operator, row):
    response = client.delete(f"{ROOT}/{row['id']}", headers=operator.headers)
    assert response.status_code == 204, response.text
    assert response.content == b""
    entries = listing(client, operator)["items"]
    return next(entry for entry in entries if entry["log_id"] == row["id"])


@pytest.fixture
def frozen_clock(monkeypatch):
    """Control only lifecycle clocks, leaving authentication/session time real."""
    from app.api.v1 import logs
    from app.services import deleted_log_service
    class Clock(datetime):
        instant = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls.instant.astimezone(tz) if tz else cls.instant.replace(tzinfo=None)
    monkeypatch.setattr(logs, "datetime", Clock)
    monkeypatch.setattr(deleted_log_service, "datetime", Clock)
    return Clock


def test_delete_snapshot_shape_seven_days_and_original_restore(api_client, owner, station_factory,
        location_factory, log_factory, db, frozen_clock):
    """04 §五 and 02 deleted_logs: exact 204, seven-day snapshot, restore original ID/data."""
    station = station_factory(owner)
    location = location_factory(owner, station)
    row = log_factory(owner, station_id=station["id"], location_id=location["id"], comment="preserve",
        grid_square="PM95AA", my_call="BA9OP", prop_mode="SAT", sat_name="TEST", srx="007", stx="008",
        contest_id="CONTEST", freq_rx=14.076, band_rx="20m", qso_date_off="2026-01-03", time_off="01:02:03")
    snapshot = delete(api_client, owner, row)
    assert set(snapshot) == {"id", "log_id", "call_sign", "qso_date", "band", "mode", "dxcc",
                             "delete_reason", "deleted_at", "expires_at", "days_remaining"}
    for field in ("call_sign", "qso_date", "band", "mode", "dxcc"):
        assert snapshot[field] == row[field]
    assert snapshot["log_id"] == row["id"]
    assert isinstance(snapshot["delete_reason"], str) and snapshot["delete_reason"]
    deleted_at = datetime.fromisoformat(snapshot["deleted_at"])
    expires_at = datetime.fromisoformat(snapshot["expires_at"])
    assert expires_at - deleted_at == timedelta(days=7)
    assert snapshot["days_remaining"] == 7
    frozen_clock.instant += timedelta(days=6, hours=12)
    page = listing(api_client, owner)
    assert (page["total"], page["page"], page["page_size"], page["pages"]) == (1, 1, 20, 1)
    assert page["items"][0]["days_remaining"] == 0
    assert api_client.get(f"{ROOT}/{row['id']}", headers=owner.headers).status_code == 404
    response = api_client.post(f"{ROOT}/recycle/{snapshot['id']}/restore", headers=owner.headers)
    assert response.status_code == 200, response.text
    restored = response.json()
    for field in ("id", "user_id", "station_id", "location_id", "call_sign", "qso_date", "time_on",
                  "comment", "grid_square", "my_call", "prop_mode", "sat_name", "srx", "stx", "contest_id",
                  "freq_rx", "band_rx", "qso_date_off", "time_off"):
        assert restored[field] == row[field]
    assert listing(api_client, owner)["items"] == []
    db.expire_all()
    assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 1
    assert db.get(DeletedLog, snapshot["id"]).is_restored is True


def test_missing_original_reconstructed_from_snapshot(api_client, owner, station_factory, location_factory, log_factory, db):
    """02 deleted_logs: only when original is missing reconstruct validated snapshot data."""
    station = station_factory(owner)
    location = location_factory(owner, station)
    row = log_factory(owner, station_id=station["id"], location_id=location["id"], comment="snapshot only",
        my_call="BA9OP", prop_mode="SAT", sat_name="SAT-X", srx="001", stx="002", contest_id="TEST",
        qso_date_off="2026-01-03", time_off="00:01:00", freq_rx=14.076)
    snapshot = delete(api_client, owner, row)
    original = db.get(QSOLog, row["id"])
    db.delete(original)
    db.commit()
    response = api_client.post(f"{ROOT}/recycle/{snapshot['id']}/restore", headers=owner.headers)
    assert response.status_code == 200, response.text
    restored = response.json()
    for field in ("user_id", "station_id", "location_id", "call_sign", "qso_date", "time_on", "freq",
                  "freq_rx", "comment", "my_call", "prop_mode", "sat_name", "srx", "stx", "contest_id",
                  "qso_date_off", "time_off"):
        assert restored[field] == row[field]
    db.expire_all()
    assert db.query(QSOLog).filter_by(user_id=owner.id, is_deleted=False).count() == 1
    assert db.get(DeletedLog, snapshot["id"]).is_restored is True


def test_expired_snapshot_is_hidden_and_rejected_without_mutation(api_client, owner, station_factory,
        log_factory, db, frozen_clock):
    """02 deleted_logs: after seven days (not ambiguous equality), reject restore without mutation."""
    station = station_factory(owner)
    row = log_factory(owner, station_id=station["id"])
    snapshot = delete(api_client, owner, row)
    frozen_clock.instant += timedelta(days=7, seconds=1)
    assert listing(api_client, owner)["total"] == 0
    response = api_client.post(f"{ROOT}/recycle/{snapshot['id']}/restore", headers=owner.headers)
    assert response.status_code == 400, response.text
    db.expire_all()
    assert db.get(QSOLog, row["id"]).is_deleted is True
    assert db.get(DeletedLog, snapshot["id"]).is_restored is False
    assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 1


@pytest.mark.parametrize("operation", ["batch-delete", "clear-all"])
def test_permanent_operations_remove_only_owned_snapshots(api_client, owner, other, station_factory,
        log_factory, db, operation):
    """04 §五 recycle: batch/clear remove backups only, preserve soft QSO rows and other owners."""
    station = station_factory(owner)
    foreign_station = station_factory(other, "BA2OTH")
    rows = [log_factory(owner, station_id=station["id"], call_sign=f"JA{i}OWN") for i in (1, 2)]
    snapshots = [delete(api_client, owner, row) for row in rows]
    foreign_row = log_factory(other, station_id=foreign_station["id"])
    foreign_snapshot = delete(api_client, other, foreign_row)
    kwargs = {"json": {"ids": [entry["id"] for entry in snapshots] + [foreign_snapshot["id"]]}} if operation == "batch-delete" else {}
    response = api_client.post(f"{ROOT}/recycle/{operation}", headers=owner.headers, **kwargs)
    assert response.status_code == 200, response.text
    assert response.json() == {"deleted": 2}
    assert listing(api_client, owner)["total"] == 0
    assert listing(api_client, other)["items"][0]["id"] == foreign_snapshot["id"]
    db.expire_all()
    for row in rows + [foreign_row]:
        assert db.get(QSOLog, row["id"]).is_deleted is True
    assert db.get(DeletedLog, foreign_snapshot["id"]).is_restored is False


def test_other_user_cannot_restore_snapshot(api_client, owner, other, station_factory, log_factory, db):
    """02 ownership and 04 §五: another user's snapshot is 404, never restored or modified."""
    station = station_factory(owner)
    row = log_factory(owner, station_id=station["id"])
    snapshot = delete(api_client, owner, row)
    assert listing(api_client, other)["total"] == 0
    response = api_client.post(f"{ROOT}/recycle/{snapshot['id']}/restore", headers=other.headers)
    assert response.status_code == 404, response.text
    db.expire_all()
    assert db.get(QSOLog, row["id"]).is_deleted is True
    assert db.get(DeletedLog, snapshot["id"]).is_restored is False
    assert listing(api_client, owner)["total"] == 1


@pytest.mark.parametrize("parent", ["station", "location"])
@pytest.mark.parametrize("missing_original", [False, True])
def test_deleted_parent_prevents_restore_and_rejection_preserves_data(api_client, owner, station_factory,
        location_factory, log_factory, db, parent, missing_original):
    """02 validated snapshot/original restore: deleted parents are 404 and never revived."""
    station = station_factory(owner)
    location = location_factory(owner, station)
    row = log_factory(owner, station_id=station["id"], location_id=location["id"], comment="untouched")
    snapshot = delete(api_client, owner, row)
    path = "stations" if parent == "station" else "locations"
    selected = station if parent == "station" else location
    response = api_client.delete(f"/api/v1/{path}/{selected['id']}", headers=owner.headers)
    assert response.status_code == 204, response.text
    if missing_original:
        db.delete(db.get(QSOLog, row["id"]))
        db.commit()
    db.expire_all()
    before = dict(db.get(DeletedLog, snapshot["id"]).log_data)
    response = api_client.post(f"{ROOT}/recycle/{snapshot['id']}/restore", headers=owner.headers)
    assert response.status_code == 404, response.text
    db.expire_all()
    entry = db.get(DeletedLog, snapshot["id"])
    assert entry.is_restored is False and entry.log_data == before
    assert db.get(Location, location["id"]).is_deleted is True
    assert db.get(Station, station["id"]).is_deleted is (parent == "station")
    if missing_original:
        assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 0
    else:
        original = db.get(QSOLog, row["id"])
        assert original.is_deleted is True and original.comment == "untouched"


def test_station_cascade_once_and_same_callsign_recreation_does_not_revive_children(api_client, owner,
        station_factory, location_factory, log_factory, db):
    """02 cascade/station revival: snapshot live logs once; recreate station only, never children."""
    station = station_factory(owner)
    locations = [location_factory(owner, station, name=name) for name in ("Home", "Portable")]
    rows = [log_factory(owner, station_id=station["id"], location_id=location["id"], call_sign=f"JA{i}LIVE")
            for i, location in enumerate(locations)]
    already_deleted = delete(api_client, owner, rows[0])
    response = api_client.delete(f"/api/v1/stations/{station['id']}", headers=owner.headers)
    assert response.status_code == 204, response.text
    entries = listing(api_client, owner)["items"]
    assert len(entries) == 2
    assert {entry["log_id"] for entry in entries} == {row["id"] for row in rows}
    assert sum(entry["id"] == already_deleted["id"] for entry in entries) == 1
    response = api_client.delete(f"/api/v1/stations/{station['id']}", headers=owner.headers)
    assert response.status_code == 404, response.text
    assert listing(api_client, owner)["total"] == 2
    recreated = station_factory(owner, station["callsign"])
    assert recreated["id"] == station["id"]
    db.expire_all()
    assert db.get(Station, station["id"]).is_deleted is False
    for location in locations:
        assert db.get(Location, location["id"]).is_deleted is True
    for row in rows:
        assert db.get(QSOLog, row["id"]).is_deleted is True
    assert listing(api_client, owner)["total"] == 2
    assert api_client.get(ROOT, headers=owner.headers).json()["total"] == 0
