"""Real HTTP/auth/service stack on an isolated database; never override authentication."""
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database.session import get_db
from app.models.user import User
from app.utils.security import SecurityUtils


PASSWORD = "Contract-password-2026"


@dataclass(frozen=True)
class Operator:
    id: int
    username: str
    token: str

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}


@pytest.fixture
def api_mode(request):
    """Mode branch only; SQLite storage is not a substitute for real MySQL coverage."""
    return getattr(request, "param", "sqlite")


@pytest.fixture
def api_app(db, monkeypatch, api_mode):
    from app import dependencies, main
    from app.api.v1 import udp
    from app.api.v1.admin import router as admin_router
    from app.database import session as database_session

    monkeypatch.setattr(settings, "DATABASE_MODE", api_mode)
    monkeypatch.setattr(settings, "QRZ_USERNAME", "")
    monkeypatch.setattr(settings, "QRZ_PASSWORD", "")
    factory = sessionmaker(bind=db.get_bind(), autoflush=False)
    for module in (dependencies, udp, database_session):
        monkeypatch.setattr(module, "SessionLocal", factory)

    def isolated_session():
        with factory() as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise

    # Copy the real application's route table, middleware and exception handlers.
    # Only admin registration depends on process-level mode, so compose that real
    # router for the server-mode branch without reloading shared application modules.
    app = FastAPI(lifespan=main.lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(main.app.router)
    if api_mode == "mysql":
        app.include_router(admin_router, prefix="/api/v1/admin")
    app.user_middleware = list(main.app.user_middleware)
    app.exception_handlers = dict(main.app.exception_handlers)
    app.dependency_overrides[get_db] = isolated_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def api_client(api_app):
    with TestClient(api_app, client=("198.51.100.20", 48000), raise_server_exceptions=False) as client:
        yield client


@pytest.fixture(scope="session")
def contract_password_hash():
    return SecurityUtils.hash_password(PASSWORD)


@pytest.fixture
def contract_password():
    return PASSWORD


@pytest.fixture
def operator_factory(api_client, db, contract_password_hash):
    def create(username="contract_owner", role="user"):
        user = User(username=username, email=f"{username}@example.com",
                    password_hash=contract_password_hash, role=role,
                    is_active=True, is_deleted=False)
        db.add(user)
        db.commit()
        response = api_client.post("/api/v1/auth/login", json={"username": username, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return Operator(user.id, username, response.json()["access_token"])
    return create


@pytest.fixture
def owner(operator_factory):
    return operator_factory()


@pytest.fixture
def other(operator_factory):
    return operator_factory("contract_other")


@pytest.fixture
def station_factory(api_client):
    def create(operator, callsign="BA1OWN"):
        response = api_client.post("/api/v1/stations", headers=operator.headers, json={"callsign": callsign})
        assert response.status_code == 201, response.text
        return response.json()
    return create


@pytest.fixture
def location_factory(api_client):
    def create(operator, station, *, name="Home", grid="OM89AA"):
        response = api_client.post("/api/v1/locations", headers=operator.headers,
                                   json={"station_id": station["id"], "name": name, "grid_square": grid})
        assert response.status_code == 201, response.text
        return response.json()
    return create


@pytest.fixture
def log_factory(api_client):
    def create(operator, **fields):
        payload = {"call_sign": "JA1ABC", "qso_date": "2026-01-02", "time_on": "12:34:56",
                   "band": "20m", "mode": "FT8", "freq": 14.074, **fields}
        response = api_client.post("/api/v1/logs", headers=operator.headers, json=payload)
        assert response.status_code == 201, response.text
        return response.json()
    return create
