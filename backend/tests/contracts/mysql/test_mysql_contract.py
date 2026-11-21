"""Actual MySQL storage: doc/02 constraints, doc/03 auth, doc/10 migration."""
from decimal import Decimal

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.models.qso_log import QSOLog
from app.models.user import User
from app.models.user_session import UserSession
from app.scripts.init_db import init_database


TABLES = {"users", "stations", "locations", "qso_logs", "callsign_cache", "statistics", "log_files",
          "sync_history", "deleted_logs", "audit_logs", "user_sessions", "system_configs", "alembic_version"}


def test_mysql_migration_initializes_empty_accounts_and_is_repeatable(db):
    engine = db.get_bind()
    assert set(inspect(engine).get_table_names()) == TABLES
    assert db.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "5eed5637c7eb"
    assert db.query(User).count() == 0
    assert db.query(UserSession).count() == 0
    db.rollback()
    init_database(database_engine=engine)
    assert db.query(User).count() == 0
    assert db.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "5eed5637c7eb"


def test_mysql_utf8_decimal_and_validated_parent_roundtrip(api_client, db, owner, station_factory, location_factory, log_factory):
    station = station_factory(owner)
    location = location_factory(owner, station, name="野外台站", grid="OM89AA")
    record = log_factory(owner, station_id=station["id"], location_id=location["id"],
                         comment="通联日志 📻", freq="14.074123", tx_pwr=25)
    saved = api_client.get(f"/api/v1/logs/{record['id']}", headers=owner.headers)
    assert saved.status_code == 200, saved.text
    assert saved.json()["comment"] == "通联日志 📻"
    assert saved.json()["location_name"] == "野外台站"
    assert Decimal(str(saved.json()["freq"])) == Decimal("14.074123")
    # End the observer's REPEATABLE READ snapshot before observing HTTP commits.
    db.rollback()
    assert db.get(QSOLog, record["id"]).freq == Decimal("14.074123")


def test_mysql_cross_user_reference_is_404_and_never_written(api_client, db, owner, other, station_factory, location_factory):
    station = station_factory(owner)
    location = location_factory(owner, station)
    before = db.query(QSOLog).count()
    rejected = api_client.post("/api/v1/logs", headers=other.headers,
                               json={"call_sign": "JA1ABC", "station_id": station["id"], "location_id": location["id"]})
    assert rejected.status_code == 404, rejected.text
    db.rollback()
    assert db.query(QSOLog).count() == before
    assert api_client.get("/api/v1/logs", headers=other.headers).json()["items"] == []


def test_mysql_logout_removes_authoritative_session(api_client, db, owner):
    assert api_client.get("/api/v1/auth/me", headers=owner.headers).status_code == 200
    response = api_client.post("/api/v1/auth/logout", headers=owner.headers)
    assert response.status_code == 200, response.text
    assert api_client.get("/api/v1/logs", headers=owner.headers).status_code == 401
    db.rollback()
    assert db.query(UserSession).filter_by(user_id=owner.id).count() == 0


def test_mysql_physical_parent_constraints_are_real(db, owner, station_factory, location_factory, log_factory):
    station = station_factory(owner)
    location = location_factory(owner, station)
    record = log_factory(owner, station_id=station["id"], location_id=location["id"])
    with pytest.raises(IntegrityError):
        db.execute(text("DELETE FROM stations WHERE id=:id"), {"id": station["id"]})
        db.commit()
    db.rollback()
    assert db.get(QSOLog, record["id"]).station_id == station["id"]
    db.execute(text("DELETE FROM locations WHERE id=:id"), {"id": location["id"]})
    db.commit()
    db.expire_all()
    assert db.get(QSOLog, record["id"]).location_id is None
    assert db.get(QSOLog, record["id"]).is_deleted is False
