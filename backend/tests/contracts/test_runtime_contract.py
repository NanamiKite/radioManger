"""Real CLI/import/release subprocess contracts, entirely inside temporary packages."""
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from contextlib import contextmanager
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest
from dotenv import dotenv_values


BACKEND = Path(__file__).resolve().parents[2]
TABLES = {
    "audit_logs", "callsign_cache", "deleted_logs", "locations", "log_files", "qso_logs",
    "stations", "statistics", "sync_history", "system_configs", "users", "user_sessions",
}
HEAD = "5eed5637c7eb"


@pytest.fixture
def staged_backend(tmp_path):
    """Copy only release code/config, never a developer database, dotenv, or uploads."""
    package = tmp_path / "package"
    backend = package / "backend"
    backend.mkdir(parents=True)
    for name in ("app", "alembic"):
        shutil.copytree(BACKEND / name, backend / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("alembic.ini", "release_server.py"):
        shutil.copy2(BACKEND / name, backend / name)
    return backend


def child_env(backend, database):
    # Deliberate allowlist: never inherit production DB URLs, tokens or proxy credentials.
    return {
        "PATH": os.defpath,
        "HOME": str(backend.parent),
        "LANG": "C.UTF-8",
        "PYTHONPATH": str(backend),
        "PYTHONUNBUFFERED": "1",
        "ENVIRONMENT": "production",
        "SECRET_KEY": secrets.token_hex(32),
        "DATABASE_MODE": "sqlite",
        "SQLITE_URL": f"sqlite:///{database}",
        "SQLITE_PATH": str(database),
        "LOG_FILE": str(backend.parent / "runtime.log"),
        "UPLOAD_DIR": str(backend.parent / "uploads"),
        "QRZ_USERNAME": "",
        "QRZ_PASSWORD": "",
        "DEBUG": "false",
        "WORKERS": "1",
    }


def run_child(backend, env, *args, success=True):
    result = subprocess.run([sys.executable, *args], cwd=backend.parent, env=env,
                            text=True, capture_output=True, timeout=30)
    if success:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, result.stdout + result.stderr
    return result


def table_names(connection):
    return {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


def assert_migrated(database):
    with sqlite3.connect(database) as connection:
        assert table_names(connection) == TABLES | {"alembic_version"}
        assert connection.execute("SELECT version_num FROM alembic_version").fetchall() == [(HEAD,)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def seed_owned_state(database):
    """Seed real persisted rows, including credentials that initialization must not reset."""
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "INSERT INTO users(id,username,email,password_hash,role,is_active,is_deleted) "
            "VALUES(41,'existing_owner','existing@example.com','preserved-password-hash','user',1,0)")
        connection.execute(
            "INSERT INTO stations(id,user_id,callsign,is_deleted) VALUES(51,41,'BA1OLD',0)")
        connection.execute(
            "INSERT INTO locations(id,user_id,station_id,name,grid_square,is_active,is_deleted) "
            "VALUES(61,41,51,'Existing home','OM89AA',1,0)")
        connection.execute(
            "INSERT INTO qso_logs(id,user_id,station_id,location_id,call_sign,qso_date,time_on,mode,is_deleted) "
            "VALUES(71,41,51,61,'JA1OLD','2026-01-02','12:34:56','FT8',0)")
        connection.execute(
            "INSERT INTO user_sessions(id,user_id,token_jti,expires_at) "
            "VALUES(81,41,'preserved-session-jti','2030-01-01 00:00:00')")
        connection.execute(
            "INSERT INTO system_configs(id,key,value,value_type,updated_by) "
            "VALUES(91,'contract_setting','preserved-setting','string',41)")


def snapshot(database):
    with sqlite3.connect(database) as connection:
        return {table: connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
                for table in sorted(table_names(connection))}


def test_importing_main_never_creates_tables(staged_backend):
    database = staged_backend.parent / "import-only.sqlite"
    env = child_env(staged_backend, database)
    run_child(staged_backend, env, "-c", "import app.main; print('IMPORT_COMPLETE')")
    with sqlite3.connect(database) as connection:
        assert table_names(connection) == set()


def test_fresh_cli_migrates_twelve_tables_to_head_without_default_accounts(staged_backend):
    database = staged_backend.parent / "fresh.sqlite"
    env = child_env(staged_backend, database)
    result = run_child(staged_backend, env, "-m", "app.scripts.init_db")
    assert_migrated(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT username FROM users").fetchall() == []
        assert connection.execute("SELECT * FROM user_sessions").fetchall() == []
    assert env["SECRET_KEY"] not in result.stdout + result.stderr


def test_repeated_cli_initialization_preserves_existing_data_and_credentials(staged_backend):
    database = staged_backend.parent / "existing.sqlite"
    env = child_env(staged_backend, database)
    run_child(staged_backend, env, "-m", "app.scripts.init_db")
    seed_owned_state(database)
    expected = snapshot(database)
    for _ in range(2):
        result = run_child(staged_backend, env, "-m", "app.scripts.init_db")
        assert snapshot(database) == expected
        assert env["SECRET_KEY"] not in result.stdout + result.stderr
        assert "preserved-password-hash" not in result.stdout + result.stderr
    assert_migrated(database)


@pytest.mark.parametrize("adopt", [False, True])
def test_wrong_legacy_schema_cli_rejects_without_stamping_or_changing_rows(staged_backend, adopt):
    database = staged_backend.parent / "wrong-legacy.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, private_value TEXT)")
        connection.execute("INSERT INTO users VALUES(7,'legacy_owner','do-not-touch')")
    before = snapshot(database)
    env = child_env(staged_backend, database)
    args = ["-m", "app.scripts.init_db"] + (["--adopt-legacy"] if adopt else [])
    result = run_child(staged_backend, env, *args, success=False)
    assert snapshot(database) == before
    with sqlite3.connect(database) as connection:
        assert "alembic_version" not in table_names(connection)
    assert env["SECRET_KEY"] not in result.stdout + result.stderr


def test_documented_online_backup_copies_committed_live_wal_rows(staged_backend):
    database = staged_backend.parent / "live.sqlite"
    backup = staged_backend.parent / "backup.sqlite"
    env = child_env(staged_backend, database)
    run_child(staged_backend, env, "-m", "app.scripts.init_db")
    # Keep the writer open with checkpointing disabled so a bare .db copy is insufficient.
    with sqlite3.connect(database) as writer:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        writer.execute("PRAGMA wal_autocheckpoint=0")
        seed_owned_state(database)
        writer.execute("UPDATE qso_logs SET comment='committed in live WAL' WHERE id=71")
        writer.commit()
        wal = Path(str(database) + "-wal")
        assert wal.is_file() and wal.stat().st_size > 32
        result = run_child(staged_backend, env, "-c", """
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as source:
    with sqlite3.connect(sys.argv[2]) as target:
        source.backup(target)
""", str(database), str(backup))
        assert result.returncode == 0
        assert snapshot(backup) == snapshot(database)
        with sqlite3.connect(backup) as copied:
            assert copied.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert copied.execute("SELECT call_sign,comment FROM qso_logs WHERE id=71").fetchone() == (
                "JA1OLD", "committed in live WAL")


def http_get(base, path):
    try:
        with urlopen(base + path, timeout=1) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except HTTPError as response:
        return response.code, response.headers.get("Content-Type", ""), response.read()


@contextmanager
def release_process(backend, env, output):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    with output.open("w+") as log:
        # Import the real release module, including its migrations and static mount.
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "release_server:application", "--host", "127.0.0.1",
             "--port", str(port), "--workers", "1"],
            cwd=backend.parent, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
        base = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + 20
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail("Release child exited before readiness:\n" + log.read())
                try:
                    status, _, _ = http_get(base, "/health")
                except (URLError, TimeoutError, ConnectionError):
                    status = None
                if status is not None:
                    assert status == 200
                    break
                if time.monotonic() >= deadline:
                    log.seek(0)
                    pytest.fail("Release child readiness timed out:\n" + log.read())
                time.sleep(0.05)
            yield base
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.parametrize("existing_secret", [True, False])
def test_real_release_entry_serves_spa_without_masking_api_and_preserves_state(staged_backend, existing_secret):
    database = staged_backend.parent / "release.sqlite"
    env = child_env(staged_backend, database)
    run_child(staged_backend, env, "-m", "app.scripts.init_db")
    seed_owned_state(database)
    expected = snapshot(database)
    frontend = staged_backend / "frontend_dist"
    (frontend / "assets").mkdir(parents=True)
    page = "<!doctype html><title>Contract SPA</title><div id='app'>Radio contract</div>"
    (frontend / "index.html").write_text(page, encoding="utf-8")
    (frontend / "assets" / "contract.js").write_text("window.contractAsset = true;", encoding="utf-8")
    secret = secrets.token_hex(32) if existing_secret else None
    env_file = staged_backend.parent / ".env"
    config = "DATABASE_MODE=sqlite\n" + f"SQLITE_URL=sqlite:///{database}\nSQLITE_PATH={database}\n"
    if secret:
        config += f"SECRET_KEY={secret}\n"
    env_file.write_text(config, encoding="utf-8")
    original_config = env_file.read_bytes()
    # The release entry must obtain its persisted settings from its own package root.
    for key in ("SECRET_KEY", "SQLITE_URL", "SQLITE_PATH", "DATABASE_MODE"):
        env.pop(key)
    for start in range(2):
        output = staged_backend.parent / f"release-{start}.log"
        with release_process(staged_backend, env, output) as base:
            for path in ("/", "/logs", "/settings/profile"):
                status, content_type, body = http_get(base, path)
                assert status == 200
                assert "text/html" in content_type
                assert body.decode() == page
            status, content_type, body = http_get(base, "/health")
            assert status == 200
            assert "application/json" in content_type
            health = json.loads(body)
            assert health["status"] == "ok"
            assert health["database"] == "sqlite"
            assert health["subsystems"]["database"] == "ok"
            status, content_type, body = http_get(base, "/assets/contract.js")
            assert status == 200
            assert body == b"window.contractAsset = true;"
            for path in ("/assets/missing.js", "/missing.css", "/api/v1/missing", "/api/missing",
                         "/health/missing", "/openapi.json/missing"):
                status, _, body = http_get(base, path)
                assert status == 404, (path, status, body)
                assert body.decode() != page
        values = dotenv_values(env_file)
        if secret is None:
            secret = values["SECRET_KEY"]
            assert len(secret) >= 32
            assert env_file.stat().st_mode & 0o077 == 0
        assert values["SECRET_KEY"] == secret
        if existing_secret:
            assert env_file.read_bytes() == original_config
        assert values["SQLITE_URL"] == f"sqlite:///{database}"
        assert snapshot(database) == expected
        captured = output.read_text(encoding="utf-8")
        assert secret not in captured
        assert "preserved-password-hash" not in captured
        assert "preserved-session-jti" not in captured
    assert_migrated(database)
