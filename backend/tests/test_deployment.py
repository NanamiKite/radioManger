"""Deployment tests use only temporary SQLite databases and frozen migration schemas."""
import ast
from pathlib import Path

import pytest
from alembic import command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from starlette.applications import Starlette
from starlette.testclient import TestClient

from app.config import Settings
from app.scripts import init_db


@pytest.mark.parametrize("packaged", [True, False])
def test_release_preserves_configuration_and_database_root(tmp_path, monkeypatch, packaged):
    import sys
    from dotenv import dotenv_values

    backend = tmp_path / "backend"
    backend.mkdir()
    if packaged:
        (backend / "frontend_dist").mkdir()
    expected_root = tmp_path if packaged else backend
    database = expected_root / "radiomanager.db"
    database.write_bytes(b"existing database marker")
    (expected_root / ".env").write_text("SECRET_KEY=\nDATABASE_MODE=sqlite\n")
    source = Path(__file__).resolve().parents[1] / "release_server.py"
    tree = ast.parse(source.read_text())
    stop = next(index for index, node in enumerate(tree.body)
                if isinstance(node, ast.ImportFrom) and node.module == "fastapi.staticfiles")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", list(sys.path))
    namespace = {"__file__": str(backend / "release_server.py")}
    exec(compile(ast.Module(body=tree.body[:stop], type_ignores=[]), str(source), "exec"), namespace)
    assert Path.cwd() == expected_root
    assert database.read_bytes() == b"existing database marker"
    first_secret = dotenv_values(expected_root / ".env")["SECRET_KEY"]
    assert len(first_secret) >= 32
    namespace["ensure_local_secret"]()
    assert dotenv_values(expected_root / ".env")["SECRET_KEY"] == first_secret


@pytest.fixture
def deployment_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'deployment.sqlite'}")
    yield engine
    engine.dispose()


def frozen_schema(role_length=20):
    script = ScriptDirectory.from_config(init_db._get_alembic_config())
    return script.get_revision(init_db.BASELINE).module.schema_metadata(role_length=role_length)


def revision(engine):
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def test_empty_database_uses_real_migrations(deployment_engine):
    init_db.init_database(database_engine=deployment_engine)
    assert revision(deployment_engine) == init_db.ORIGINAL_HEAD
    assert set(inspect(deployment_engine).get_table_names()) == set(frozen_schema().tables) | {"alembic_version"}
    with deployment_engine.connect() as connection:
        assert not init_db._schema_differences(connection, frozen_schema())


def test_previously_stamped_head_remains_valid(deployment_engine):
    frozen_schema().create_all(deployment_engine)
    with deployment_engine.begin() as connection:
        command.stamp(init_db._get_alembic_config(connection), init_db.ORIGINAL_HEAD)
    init_db.init_database(database_engine=deployment_engine)
    assert revision(deployment_engine) == init_db.ORIGINAL_HEAD


@pytest.mark.parametrize("role_length", [5, 20])
def test_legacy_adoption_is_explicit_and_verified(deployment_engine, role_length):
    frozen_schema(role_length).create_all(deployment_engine)
    with pytest.raises(RuntimeError, match="--adopt-legacy"):
        init_db.init_database(database_engine=deployment_engine)
    assert revision(deployment_engine) is None
    init_db.init_database(adopt_legacy=True, database_engine=deployment_engine)
    assert revision(deployment_engine) == init_db.ORIGINAL_HEAD


@pytest.mark.parametrize("damage", [
    "DROP INDEX ix_users_email",
    "ALTER TABLE users ADD COLUMN unexpected VARCHAR(10)",
    "DROP TABLE audit_logs",
])
def test_legacy_schema_mismatch_is_never_stamped(deployment_engine, damage):
    frozen_schema().create_all(deployment_engine)
    with deployment_engine.begin() as connection:
        connection.execute(text(damage))
    with pytest.raises(RuntimeError, match="nothing was stamped"):
        init_db.init_database(adopt_legacy=True, database_engine=deployment_engine)
    assert revision(deployment_engine) is None


def test_failed_upgrade_is_not_hidden_or_stamped(deployment_engine, monkeypatch):
    def fail_upgrade(*args, **kwargs):
        raise RuntimeError("deliberate migration failure")
    monkeypatch.setattr(init_db.command, "upgrade", fail_upgrade)
    with pytest.raises(RuntimeError, match="deliberate migration failure"):
        init_db.init_database(database_engine=deployment_engine)
    assert revision(deployment_engine) is None
    assert not inspect(deployment_engine).has_table("users")


def test_baseline_adoption_preserves_populated_owner_rows(deployment_engine):
    frozen_schema(5).create_all(deployment_engine)
    with deployment_engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.execute(text("INSERT INTO users (id,username,email,password_hash,role) VALUES (1,'owner','owner@example.com','hash','user')"))
        connection.execute(text("INSERT INTO stations (id,user_id,callsign) VALUES (1,1,'TEST')"))
    init_db.init_database(adopt_legacy=True, database_engine=deployment_engine)
    with deployment_engine.connect() as connection:
        assert connection.execute(text("SELECT username FROM users WHERE id=1")).scalar_one() == "owner"
        assert connection.execute(text("SELECT user_id FROM stations WHERE id=1")).scalar_one() == 1
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []


def test_admin_creation_rejects_non_admin_name_without_mutating(db, users, monkeypatch):
    from app.scripts import create_admin

    # The function owns its session; use a separate real session on the fixture's temporary DB.
    from sqlalchemy.orm import sessionmaker
    monkeypatch.setattr(create_admin, "SessionLocal", sessionmaker(bind=db.get_bind()))
    with pytest.raises(ValueError, match="non-admin"):
        create_admin.create_admin(users[0].username, "a-valid-password", "other@example.com")
    db.expire_all()
    assert users[0].role == "user"


@pytest.mark.parametrize("damage", ["type", "nullable", "foreign_key", "unique", "primary_key"])
def test_legacy_column_and_constraint_drift_refused(deployment_engine, damage):
    from sqlalchemy import String

    metadata = frozen_schema()
    if damage == "type":
        metadata.tables["users"].c.username.type = String(17)
    elif damage == "nullable":
        metadata.tables["users"].c.username.nullable = True
    elif damage == "foreign_key":
        table = metadata.tables["locations"]
        constraint = next(item for item in table.foreign_key_constraints if "station_id" in item.column_keys)
        table.constraints.remove(constraint)
    elif damage == "unique":
        index = next(item for item in metadata.tables["users"].indexes if item.name == "ix_users_email")
        index.unique = False
    metadata.create_all(deployment_engine)
    if damage == "primary_key":
        with deployment_engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE users_without_pk AS SELECT * FROM users")
            connection.exec_driver_sql("DROP TABLE users")
            connection.exec_driver_sql("ALTER TABLE users_without_pk RENAME TO users")
    with pytest.raises(RuntimeError, match="nothing was stamped"):
        init_db.init_database(adopt_legacy=True, database_engine=deployment_engine)
    assert revision(deployment_engine) is None

@pytest.mark.parametrize("overrides", [
    {"SECRET_KEY": ""},
    {"SECRET_KEY": "short"},
    {"SECRET_KEY": "your-super-secret-key-change-this-in-production"},
    {"SECRET_KEY": "change-" * 10},
    {"SECRET_KEY": "placeholder" * 5},
    {"ENABLE_TEST_ACCOUNT": True, "TEST_ACCOUNT_PASSWORD": "explicit-password"},
    {"DATABASE_MODE": "mysql", "DATABASE_URL": ""},
    {"DATABASE_MODE": "postgres"},
    {"WORKERS": 2},
    {"ENVIRONMENT": "invalid"},
    {"ADMIN_PASSWORD": "short"},
    {"ADMIN_PASSWORD": "é" * 37},
    {"UDP_WSJTX_PORT": 80},
    {"DX_CLUSTER_NODES": ["host-without-port"]},
    {"DX_CLUSTER_NODES": ["https://example.com:7300"]},
    {"DX_CLUSTER_NODES": ["host:0"]},
])
def test_settings_reject_unsafe_deployment(overrides):
    values = {"ENVIRONMENT": "production", "SECRET_KEY": "a" * 64}
    values.update(overrides)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_development_missing_secret_warns_and_generates():
    with pytest.warns(UserWarning, match="ephemeral"):
        settings = Settings(_env_file=None, ENVIRONMENT="development", SECRET_KEY="")
    assert len(settings.SECRET_KEY) >= 32
    assert settings.WORKERS == 1
    assert settings.MAX_UPLOAD_SIZE == 50 * 1024 * 1024


def test_configured_dx_nodes_accept_explicit_ipv4_and_ipv6():
    settings = Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="b" * 64,
                        DX_CLUSTER_NODES=["cluster.example.com:7300", "127.0.0.1:7300", "[::1]:7300"])
    assert settings.DX_CLUSTER_NODES[-1] == "[::1]:7300"


def test_packaged_static_files_do_not_escape_or_hide_api(tmp_path):
    # Extract the real route class without executing the release module's startup migrations.
    from fastapi.staticfiles import StaticFiles
    from starlette.exceptions import HTTPException
    source = Path(__file__).resolve().parents[1] / "release_server.py"
    tree = ast.parse(source.read_text())
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "SPAStaticFiles")
    namespace = {"StaticFiles": StaticFiles, "HTTPException": HTTPException, "Path": Path}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("SPA index")
    (tmp_path / "secret.txt").write_text("private credential")
    (dist / "escape.txt").symlink_to(tmp_path / "secret.txt")
    app = Starlette()
    app.mount("/", namespace["SPAStaticFiles"](directory=dist))
    with TestClient(app) as client:
        assert client.get("/dashboard").text == "SPA index"
        for path in ("/%2e%2e/secret.txt", "/escape.txt", "/api/missing", "/assets/missing.js", "/health"):
            response = client.get(path)
            assert response.status_code == 404
            assert "private credential" not in response.text
            assert response.text != "SPA index"
        assert client.post("/dashboard").status_code == 405
        assert client.head("/dashboard").status_code == 200
