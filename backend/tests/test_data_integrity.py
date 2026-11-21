from datetime import date

import pytest
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from app.exceptions import NotFoundException, ValidationException
from app.models.deleted_log import DeletedLog
from app.models.location import Location
from app.models.log_file import LogFile
from app.models.qso_log import QSOLog
from app.models.station import Station
from app.schemas.location import LocationCreate
from app.schemas.qso_log import QSOLogCreate, QSOLogUpdate
from app.services.deleted_log_service import DeletedLogService
from app.services.import_export_service import ImportExportService
from app.services.location_service import LocationService
from app.services.log_service import LogService
from app.services.station_service import StationService


def station(db, user, callsign):
    row = Station(user_id=user.id, callsign=callsign)
    db.add(row)
    db.commit()
    return row


def location(db, user, stn, name="Home"):
    return LocationService.create_location(db, user.id, LocationCreate(
        station_id=stn.id, name=name, grid_square="OM89AA"
    ))


def record(call="BH1AAA", **extra):
    values = {"call": call, "qso_date": "20260102", "time_on": "123456",
              "band": "20m", "mode": "FT8", "freq": "14.074", **extra}
    return " ".join(f"<{key}:{len(str(value))}>{value}" for key, value in values.items()) + " <eor>\n"


def test_foreign_station_and_location_are_rejected(db, users):
    owner, other = users
    own = station(db, owner, "BH1OWN")
    foreign = station(db, other, "BH1OTH")
    own_location = location(db, owner, own)
    foreign_location = location(db, other, foreign)
    with pytest.raises(NotFoundException):
        location(db, owner, foreign)
    with pytest.raises(NotFoundException):
        LogService.create_log(db, owner.id, QSOLogCreate(station_id=foreign.id, call_sign="BH1AAA"))
    with pytest.raises(NotFoundException):
        LogService.create_log(db, owner.id, QSOLogCreate(
            station_id=own.id, location_id=foreign_location.id, call_sign="BH1AAA"
        ))
    log = LogService.create_log(db, owner.id, QSOLogCreate(
        station_id=own.id, location_id=own_location.id, call_sign="BH1AAA"
    ))
    with pytest.raises(NotFoundException):
        LogService.update_log(db, log.id, owner.id, QSOLogUpdate(location_id=foreign_location.id))
    with pytest.raises(NotFoundException):
        LogService.update_log(db, log.id, owner.id, QSOLogUpdate(station_id=foreign.id))
    with pytest.raises(NotFoundException):
        ImportExportService.import_adi(db, owner.id, record(), "sample.adi", foreign.id)
    with pytest.raises(NotFoundException):
        ImportExportService.export_adi(db, owner.id, station_id=foreign.id)
    with pytest.raises(NotFoundException):
        ImportExportService.export_adi(db, owner.id, location_id=foreign_location.id)


def test_station_location_mismatch_is_rejected(db, users):
    owner = users[0]
    first = station(db, owner, "BH1ONE")
    second = station(db, owner, "BH1TWO")
    loc = location(db, owner, second)
    with pytest.raises(ValidationException):
        LogService.create_log(db, owner.id, QSOLogCreate(
            station_id=first.id, location_id=loc.id, call_sign="BH1AAA"
        ))
    with pytest.raises(ValidationException):
        ImportExportService.export_adi(db, owner.id, station_id=first.id, location_id=loc.id)


def test_same_file_duplicates_merge_across_batch_and_roundtrip(db, users):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    content = record(tx_pwr="25", my_call="BH1OWN", prop_mode="SAT", sat_name="QO-100",
                     srx="001", stx="002", contest_id="TEST") + record(comment="before")
    content += "".join(record(call=f"B{i:04d}") for i in range(499))
    content += record(lotw_rcvd="Y", eqsl_rcvd="Y")
    result = ImportExportService.import_adi(db, owner.id, content, "sample.adi", stn.id)
    assert result["imported"] == 500
    assert result["duplicates"] == 2
    assert result["merged"] == 2
    log = db.query(QSOLog).filter_by(user_id=owner.id, call_sign="BH1AAA").one()
    assert log.comment == "before"
    assert log.tx_pwr == 25
    assert log.lotw_rcvd == log.eqsl_rcvd == "Y"
    exported, _ = ImportExportService.export_adi(db, owner.id, station_id=stn.id)
    assert "<tx_pwr:2>25" in exported
    assert "<lotw_rcvd:1>Y" in exported
    assert "<eqsl_rcvd:1>Y" in exported
    imported = ImportExportService.import_adi(db, users[1].id, exported, "roundtrip.adi",
                                            station(db, users[1], "BH1OTH").id)
    assert imported["imported"] == 500
    copied = db.query(QSOLog).filter_by(user_id=users[1].id, call_sign="BH1AAA").one()
    assert copied.tx_pwr == 25
    assert copied.lotw_rcvd == copied.eqsl_rcvd == "Y"
    assert copied.my_call == "BH1OWN"
    assert copied.prop_mode == "SAT"
    assert copied.sat_name == "QO-100"
    assert copied.srx == "001"
    assert copied.stx == "002"
    assert copied.contest_id == "TEST"


def test_failed_batch_reports_only_committed_rows(db, users, monkeypatch):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    original_commit = db.commit
    calls = 0

    def fail_second_batch():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OperationalError("injected", {}, RuntimeError("batch failed"))
        original_commit()

    monkeypatch.setattr(db, "commit", fail_second_batch)
    result = ImportExportService.import_adi(
        db, owner.id, "".join(record(call=f"B{i:04d}") for i in range(501)), "failure.adi", stn.id
    )
    assert result["status"] == "partial"
    assert result["imported"] == 500
    assert db.query(QSOLog).filter_by(user_id=owner.id).count() == 500
    metadata = db.get(LogFile, result["file_id"])
    assert metadata.qso_count == 500
    assert metadata.import_status == "partial"
    assert "rolled back" in metadata.import_error


def test_malformed_fields_do_not_poison_batch(db, users):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    content = record(call="B" * 21) + record(tx_pwr="2147483648") + record(freq="10000") + record(tx_pwr="10")
    result = ImportExportService.import_adi(db, owner.id, content, "invalid.adi", stn.id)
    assert result["skipped"] == 3
    assert result["imported"] == 1
    assert db.query(QSOLog).filter_by(user_id=owner.id).one().tx_pwr == 10


def test_station_deletion_rolls_back_snapshots_and_soft_deletes(db, users):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    loc = location(db, owner, stn)
    log = LogService.create_log(db, owner.id, QSOLogCreate(
        station_id=stn.id, location_id=loc.id, call_sign="BH1AAA", qso_date=date(2026, 1, 2)
    ))
    ids = stn.id, loc.id, log.id

    def fail_commit(session):
        raise OperationalError("injected", {}, RuntimeError("commit failed"))

    event.listen(db, "before_commit", fail_commit)
    try:
        with pytest.raises(OperationalError):
            StationService.delete_station(db, ids[0], owner.id)
    finally:
        event.remove(db, "before_commit", fail_commit)
    assert not db.get(Station, ids[0]).is_deleted
    assert not db.get(Location, ids[1]).is_deleted
    assert not db.get(QSOLog, ids[2]).is_deleted
    assert db.query(DeletedLog).filter_by(user_id=owner.id).count() == 0


def test_restore_refuses_deleted_parent(db, users):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    loc = location(db, owner, stn)
    LogService.create_log(db, owner.id, QSOLogCreate(
        station_id=stn.id, location_id=loc.id, call_sign="BH1AAA"
    ))
    StationService.delete_station(db, stn.id, owner.id)
    entry = db.query(DeletedLog).filter_by(user_id=owner.id).one()
    with pytest.raises(NotFoundException):
        DeletedLogService.restore_log(db, entry.id, owner.id)
    assert not entry.is_restored
    assert db.get(Station, stn.id).is_deleted
    assert db.get(Location, loc.id).is_deleted


def test_restore_refuses_deleted_location(db, users):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    loc = location(db, owner, stn)
    log = LogService.create_log(db, owner.id, QSOLogCreate(
        station_id=stn.id, location_id=loc.id, call_sign="BH1AAA"
    ))
    LogService.delete_log(db, log.id, owner.id)
    LocationService.delete_location(db, loc.id, owner.id)
    entry = db.query(DeletedLog).filter_by(user_id=owner.id).one()
    with pytest.raises(NotFoundException):
        DeletedLogService.restore_log(db, entry.id, owner.id)
    assert not entry.is_restored
    assert db.get(QSOLog, log.id).is_deleted


def test_enrichment_never_exposes_foreign_historical_links(db, users):
    from app.api.v1.logs import _build_location_cache, _build_station_cache

    owner, other = users
    foreign = station(db, other, "BH1OTH")
    foreign_loc = location(db, other, foreign)
    corrupt = QSOLog(user_id=owner.id, station_id=foreign.id, location_id=foreign_loc.id,
                     call_sign="BH1BAD", qso_date=date(2026, 1, 2))
    db.add(corrupt)
    db.commit()
    assert _build_station_cache(db, owner.id, [corrupt]) == {}
    assert _build_location_cache(db, owner.id, [corrupt]) == {}
    assert _build_station_cache(db, other.id, []) == {}
    assert _build_location_cache(db, other.id, []) == {}


def test_import_deduplicates_across_owned_stations(db, users):
    owner = users[0]
    first = station(db, owner, "BH1ONE")
    second = station(db, owner, "BH1TWO")
    ImportExportService.import_adi(db, owner.id, record(), "first.adi", first.id)
    result = ImportExportService.import_adi(db, owner.id, record(comment="merged"), "second.adi", second.id)
    assert result["imported"] == 0
    assert result["duplicates"] == result["merged"] == 1
    log = db.query(QSOLog).filter_by(user_id=owner.id).one()
    assert log.station_id == first.id
    assert log.comment == "merged"


def test_export_location_keeps_grid_prefix_semantics(db, users):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    loc = location(db, owner, stn)
    db.add_all([
        QSOLog(user_id=owner.id, station_id=stn.id, location_id=None,
               call_sign="BH1YES", qso_date=date(2026, 1, 2), my_gridsquare="OM89BB"),
        QSOLog(user_id=owner.id, station_id=stn.id, location_id=loc.id,
               call_sign="BH1NO", qso_date=date(2026, 1, 2), my_gridsquare="OM88AA"),
    ])
    db.commit()
    exported, _ = ImportExportService.export_adi(db, owner.id, location_id=loc.id)
    assert "BH1YES" in exported
    assert "BH1NO" not in exported


def test_create_station_revives_same_deleted_callsign(db, users):
    from app.schemas.station import StationCreate

    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    StationService.delete_station(db, stn.id, owner.id)
    revived = StationService.create_station(db, owner.id, StationCreate(callsign="bh1own"))
    assert revived.id == stn.id
    assert not revived.is_deleted
    with pytest.raises(ValidationException):
        StationService.create_station(db, owner.id, StationCreate(callsign="BH1OWN"))


@pytest.mark.parametrize("invalid_snapshot", [False, True])
def test_restore_reconstructs_only_valid_snapshot(db, users, invalid_snapshot):
    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    loc = location(db, owner, stn)
    log = LogService.create_log(db, owner.id, QSOLogCreate(
        station_id=stn.id, location_id=loc.id, call_sign="BH1AAA", tx_pwr=25
    ))
    LogService.delete_log(db, log.id, owner.id)
    entry = db.query(DeletedLog).filter_by(user_id=owner.id).one()
    db.delete(log)
    if invalid_snapshot:
        entry.log_data = {**entry.log_data, "qso_date": "invalid"}
    else:
        entry.log_data = {**entry.log_data, "qso_date": "20260102", "time_on": "123456"}
    db.commit()
    if invalid_snapshot:
        with pytest.raises(ValidationException):
            DeletedLogService.restore_log(db, entry.id, owner.id)
        assert not entry.is_restored
    else:
        restored = DeletedLogService.restore_log(db, entry.id, owner.id)
        assert restored.tx_pwr == 25
        assert restored.station_id == stn.id
        assert restored.location_id == loc.id
        assert restored.qso_date == date(2026, 1, 2)
        assert restored.time_on.strftime("%H%M%S") == "123456"


def test_import_route_reports_database_failure_with_committed_counts(db, users, monkeypatch):
    import asyncio
    import io
    import json
    from fastapi import UploadFile
    from app.api.v1.logs import import_logs

    owner = users[0]
    stn = station(db, owner, "BH1OWN")
    original_commit = db.commit
    calls = 0

    def fail_second_batch():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OperationalError("injected", {}, RuntimeError("batch failed"))
        original_commit()

    monkeypatch.setattr(db, "commit", fail_second_batch)
    upload = UploadFile(filename="input.ADI", file=io.BytesIO(
        "".join(record(call=f"B{i:04d}") for i in range(501)).encode()
    ))
    response = asyncio.run(import_logs(file=upload, station_id=stn.id, db=db, current_user=owner))
    assert response.status_code == 503
    result = json.loads(response.body)
    assert result["database_failed"] is True
    assert result["imported"] == 500
    assert result["status"] == "partial"
