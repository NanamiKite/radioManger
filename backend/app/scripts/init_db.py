"""Explicit deployment migrations; legacy adoption never repairs or guesses schema."""
import argparse
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.database.base import engine

BASELINE = "000000000001"
ORIGINAL_HEAD = "5eed5637c7eb"


def _get_alembic_config(connection=None):
    backend = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    cfg.attributes.update(configure_loggers=False, use_settings_url=False)
    if connection is not None:
        cfg.attributes["connection"] = connection
    return cfg


def _schema_differences(connection, metadata):
    context = MigrationContext.configure(connection, opts={"compare_type": True})
    differences = compare_metadata(context, metadata)
    inspector = inspect(connection)
    for table in metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        actual = inspector.get_pk_constraint(table.name).get("constrained_columns", [])
        expected = [column.name for column in table.primary_key]
        if actual != expected:
            differences.append(("primary_key", table.name, actual, expected))
        actual_checks = {item["sqltext"].strip() for item in inspector.get_check_constraints(table.name)}
        expected_checks = {str(item.sqltext).strip() for item in table.constraints if hasattr(item, "sqltext")}
        if actual_checks != expected_checks:
            differences.append(("check_constraints", table.name, actual_checks, expected_checks))
    return differences


def _report_cross_owner_rows(connection):
    queries = {
        "locations.station_owner": "SELECT count(*) FROM locations l JOIN stations s ON l.station_id=s.id WHERE l.user_id<>s.user_id",
        "qso_logs.station_owner": "SELECT count(*) FROM qso_logs q JOIN stations s ON q.station_id=s.id WHERE q.user_id<>s.user_id",
        "qso_logs.location_owner": "SELECT count(*) FROM qso_logs q JOIN locations l ON q.location_id=l.id WHERE q.user_id<>l.user_id OR q.station_id<>l.station_id",
    }
    for label, query in queries.items():
        count = connection.execute(text(query)).scalar_one()
        print(f"Integrity report: {label}={count} (no data changed)")


@contextmanager
def _migration_connection(target):
    # SQLite batch migrations must replace referenced tables with FK checks disabled.
    # This is connection-local, restored even on failure; it never repairs application rows.
    with target.connect() as connection:
        foreign_keys = None
        if connection.dialect.name == "sqlite":
            foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
        try:
            with connection.begin():
                yield connection
        finally:
            if foreign_keys is not None:
                connection.exec_driver_sql(f"PRAGMA foreign_keys={int(foreign_keys)}")
                connection.commit()


def init_database(*, adopt_legacy=False, database_engine=None):
    """Upgrade an empty/versioned database, or explicitly adopt a proven legacy schema."""
    target = database_engine if database_engine is not None else engine
    with _migration_connection(target) as connection:
        cfg = _get_alembic_config(connection)
        scripts = ScriptDirectory.from_config(cfg)
        frozen = scripts.get_revision(BASELINE).module.schema_metadata
        tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
        current = MigrationContext.configure(connection).get_current_revision()
        if tables and current is None:
            if not adopt_legacy:
                raise RuntimeError("Unversioned database: back up your database, then run python -m app.scripts.init_db --adopt-legacy to verify and adopt it")
            head_diff = _schema_differences(connection, frozen(role_length=20))
            baseline_diff = _schema_differences(connection, frozen())
            if not head_diff:
                revision = ORIGINAL_HEAD
            elif not baseline_diff:
                revision = BASELINE
            else:
                raise RuntimeError(f"Legacy schema does not match head: {head_diff!r}; baseline: {baseline_diff!r}. Restore/migrate the schema explicitly before adoption; nothing was stamped")
            _report_cross_owner_rows(connection)
            command.stamp(cfg, revision)
        elif current in (BASELINE, ORIGINAL_HEAD):
            differences = _schema_differences(connection, frozen(role_length=5 if current == BASELINE else 20))
            if differences:
                raise RuntimeError(f"Versioned database schema mismatch: {differences!r}; repair through an explicit reviewed migration")
            _report_cross_owner_rows(connection)
        command.upgrade(cfg, "head")
    print("Database migrations complete. Register an account on first use, or explicitly run app.scripts.create_admin.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adopt-legacy", action="store_true")
    init_database(adopt_legacy=parser.parse_args().adopt_legacy)
