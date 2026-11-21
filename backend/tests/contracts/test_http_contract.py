"""HTTP: doc/03 response/status/rate contract; middleware remains enabled."""
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError


def test_all_business_resources_require_bearer(api_client):
    for path in ("auth/me", "users/me", "stations", "locations", "logs", "stats/overview",
                 "callsigns/JA1ABC", "map/grids", "dxcluster/status", "udp/status", "shortcuts", "sync/history"):
        response = api_client.get(f"/api/v1/{path}")
        assert response.status_code == 401, (path, response.text)


def test_normal_rate_limit_exact_edge_and_client_isolation(api_client, api_app):
    for index in range(100):
        response = api_client.get("/api/v1/logs")
        assert response.status_code == 401, (index, response.text)
    response = api_client.get("/api/v1/logs")
    assert response.status_code == 429, response.text
    assert response.json() == {"code": 429, "message": "Too many requests. Please try again later.", "data": None}
    with TestClient(api_app, client=("198.51.100.22", 48002)) as other_client:
        assert other_client.get("/api/v1/logs").status_code == 401
    # Public diagnostics stay available while a business bucket is exhausted.
    assert api_client.get("/health").status_code == 200
    assert api_client.get("/").status_code == 200


def test_sensitive_paths_share_five_request_bucket(api_client):
    for index in range(5):
        response = api_client.post("/api/v1/auth/login", json={"username": "missing", "password": "bad"})
        assert response.status_code == 401, (index, response.text)
    payload = {"username": "not_created", "email": "missing@example.com",
               "password": "contract-password", "confirm_password": "contract-password"}
    assert api_client.post("/api/v1/auth/register", json=payload).status_code == 429
    # The general request bucket is separate from the sensitive one.
    assert api_client.get("/api/v1/logs").status_code == 401


def test_forwarded_header_cannot_reset_sensitive_limit(api_client):
    for index in range(5):
        response = api_client.post("/api/v1/auth/login", headers={"X-Forwarded-For": f"203.0.113.{index + 1}"},
                                   json={"username": "missing", "password": "bad"})
        assert response.status_code == 401, response.text
    response = api_client.post("/api/v1/auth/login", headers={"X-Forwarded-For": "203.0.113.250"},
                               json={"username": "missing", "password": "bad"})
    assert response.status_code == 429, response.text


def test_health_reports_database_ok_and_failure(api_client, db):
    healthy = api_client.get("/health")
    assert healthy.status_code == 200, healthy.text
    body = healthy.json()
    assert body["status"] == "ok"
    assert body["database"] == "sqlite"
    assert body["subsystems"]["database"] == "ok"
    assert "db_path" in body and "db_dir" in body

    def offline(*args, **kwargs):
        raise OperationalError("contract injected database fault", {}, RuntimeError("offline"))

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", offline)
    try:
        failed = api_client.get("/health")
    finally:
        event.remove(engine, "before_cursor_execute", offline)
    assert failed.status_code == 503, failed.text
    assert failed.json()["status"] == "degraded"
    assert failed.json()["subsystems"]["database"] == "error"


def test_database_failure_is_not_401_or_success(api_client, db, owner):
    def offline(*args, **kwargs):
        raise OperationalError("contract injected database fault", {}, RuntimeError("offline"))

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", offline)
    try:
        response = api_client.get("/api/v1/auth/me", headers=owner.headers)
    finally:
        event.remove(engine, "before_cursor_execute", offline)
    assert response.status_code == 503, response.text
