"""AUTH: doc/03 认证方式; doc/04 一、十二、十四. Expected results precede execution."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.models.user import User
from app.models.user_session import UserSession


@pytest.mark.parametrize("username,expected", [("ab", 422), ("abc", 201), ("u" * 50, 201), ("u" * 51, 422)])
def test_registration_username_boundaries(api_client, db, contract_password, username, expected):
    response = api_client.post("/api/v1/auth/register", json={
        "username": username, "email": "new@example.com", "password": contract_password,
        "confirm_password": contract_password,
    })
    assert response.status_code == expected, response.text
    rows = db.query(User).filter_by(email="new@example.com").all()
    if expected == 201:
        assert len(rows) == 1
        body = response.json()
        assert body["id"] == rows[0].id
        assert body["username"] == username
        assert body["role"] == "user"
        assert body["is_active"] is True
        assert body["timezone"] == "UTC"
        assert body["language"] == "zh-CN"
        assert "password" not in body and "password_hash" not in body
        assert rows[0].password_hash != contract_password
    else:
        assert rows == []


@pytest.mark.parametrize("password,expected", [
    ("a" * 7, 422), ("a" * 8, 201), ("a" * 72, 201), ("a" * 73, 422),
    ("界" * 24, 201), ("界" * 24 + "a", 422),
])
def test_registration_character_and_utf8_byte_limits(api_client, db, password, expected):
    response = api_client.post("/api/v1/auth/register", json={
        "username": "password_edge", "email": "edge@example.com", "password": password,
        "confirm_password": password,
    })
    assert response.status_code == expected, response.text
    if expected == 201:
        login = api_client.post("/api/v1/auth/login", json={"username": "password_edge", "password": password})
        assert login.status_code == 200, login.text
        assert login.json()["user"]["id"] == response.json()["id"]
    else:
        assert db.query(User).filter_by(username="password_edge").count() == 0


@pytest.mark.parametrize("change", ["mismatch", "email"])
def test_invalid_registration_does_not_create_account(api_client, db, contract_password, change):
    payload = {"username": "invalid_account", "email": "invalid@example.com",
               "password": contract_password, "confirm_password": contract_password}
    payload.update({"confirm_password": "different-password"} if change == "mismatch" else {"email": "not-an-email"})
    response = api_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422, response.text
    assert db.query(User).filter_by(username="invalid_account").count() == 0


@pytest.mark.parametrize("field", ["username", "email"])
@pytest.mark.parametrize("deleted", [False, True])
def test_registered_identity_conflicts_include_deleted_users(api_client, db, owner, contract_password, field, deleted):
    if deleted:
        db.get(User, owner.id).is_deleted = True
        db.commit()
    before = db.query(User).count()
    payload = {"username": "new_identity", "email": "new@example.com", "password": contract_password,
               "confirm_password": contract_password}
    payload[field] = owner.username if field == "username" else f"{owner.username}@example.com"
    response = api_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409, response.text
    assert db.query(User).count() == before


@pytest.mark.parametrize("api_mode", ["sqlite", "mysql"], indirect=True)
def test_login_contract_and_remember_me_does_not_extend_lifetime(api_client, db, owner, contract_password):
    before = datetime.now(timezone.utc).timestamp()
    response = api_client.post("/api/v1/auth/login", json={
        "username": owner.username, "password": contract_password, "remember_me": True,
    })
    after = datetime.now(timezone.utc).timestamp()
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"access_token", "token_type", "expires_in", "user"}
    assert body["expires_in"] == 7 * 24 * 60 * 60
    assert body["token_type"] == "Bearer"
    claims = jwt.decode(body["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    assert claims["sub"] == str(owner.id)
    assert claims["token_type"] == "access"
    assert before + body["expires_in"] - 1 <= claims["exp"] <= after + body["expires_in"]
    session = db.query(UserSession).filter_by(token_jti=claims["jti"]).one()
    assert session.user_id == owner.id
    assert session.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
    assert set(body["user"]) == {"id", "username", "email", "full_name", "timezone", "language", "role", "is_active", "created_at"}


@pytest.mark.parametrize("state", ["wrong_password", "missing", "disabled", "deleted"])
def test_login_denies_invalid_identity_without_new_session(api_client, db, owner, contract_password, state):
    username, password = owner.username, contract_password
    if state == "wrong_password":
        password = "wrong-password"
    elif state == "missing":
        username = "missing_operator"
    else:
        user = db.get(User, owner.id)
        if state == "disabled":
            user.is_active = False
        else:
            user.is_deleted = True
        db.commit()
    before = db.query(UserSession).count()
    response = api_client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 401, response.text
    assert db.query(UserSession).count() == before


@pytest.mark.parametrize("api_mode", ["sqlite", "mysql"], indirect=True)
def test_logout_revokes_only_selected_session(api_client, db, owner, contract_password):
    second = api_client.post("/api/v1/auth/login", json={"username": owner.username, "password": contract_password})
    assert second.status_code == 200, second.text
    second_headers = {"Authorization": f"Bearer {second.json()['access_token']}"}
    response = api_client.post("/api/v1/auth/logout", headers=owner.headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Logout successful"}
    assert api_client.get("/api/v1/auth/me", headers=owner.headers).status_code == 401
    assert api_client.get("/api/v1/auth/me", headers=second_headers).json()["id"] == owner.id
    assert db.query(UserSession).filter_by(user_id=owner.id).count() == 1


@pytest.mark.parametrize("api_mode", ["sqlite", "mysql"], indirect=True)
def test_password_change_revokes_every_session_and_old_password(api_client, db, owner, contract_password):
    second = api_client.post("/api/v1/auth/login", json={"username": owner.username, "password": contract_password})
    assert second.status_code == 200, second.text
    new_password = "contract-new-password"
    response = api_client.post("/api/v1/auth/change-password", headers=owner.headers, json={
        "old_password": contract_password, "new_password": new_password, "confirm_password": new_password,
    })
    assert response.status_code == 200, response.text
    for token in (owner.token, second.json()["access_token"]):
        assert api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert db.query(UserSession).filter_by(user_id=owner.id).count() == 0
    # A different client IP keeps these credential assertions independent of the
    # documented shared five-request authentication rate bucket.
    from fastapi.testclient import TestClient
    with TestClient(api_client.app, client=("198.51.100.21", 48001), raise_server_exceptions=False) as fresh:
        assert fresh.post("/api/v1/auth/login", json={"username": owner.username, "password": contract_password}).status_code == 401
        success = fresh.post("/api/v1/auth/login", json={"username": owner.username, "password": new_password})
        assert success.status_code == 200, success.text
        assert success.json()["user"]["id"] == owner.id


@pytest.mark.parametrize("new_password", ["a" * 7, "a" * 73, "界" * 24 + "a"])
def test_rejected_password_change_leaves_password_and_session(api_client, db, owner, contract_password, new_password):
    original_hash = db.get(User, owner.id).password_hash
    response = api_client.post("/api/v1/auth/change-password", headers=owner.headers, json={
        "old_password": contract_password, "new_password": new_password, "confirm_password": new_password,
    })
    assert response.status_code == 422, response.text
    db.expire_all()
    assert db.get(User, owner.id).password_hash == original_hash
    assert api_client.get("/api/v1/auth/me", headers=owner.headers).status_code == 200


@pytest.mark.parametrize("api_mode", ["mysql"], indirect=True)
@pytest.mark.parametrize("action", ["reset-password", "toggle", "delete"])
def test_admin_mutations_invalidate_subject_sessions(api_client, db, owner, operator_factory, action):
    admin = operator_factory("contract_admin", role="admin")
    if action == "delete":
        response = api_client.delete(f"/api/v1/admin/users/{owner.id}", headers=admin.headers)
    else:
        response = api_client.post(f"/api/v1/admin/users/{owner.id}/{action}", headers=admin.headers,
                                   json={"new_password": "admin-new-password"} if action == "reset-password" else None)
    assert response.status_code == 200, response.text
    assert api_client.get("/api/v1/auth/me", headers=owner.headers).status_code == 401
    assert db.query(UserSession).filter_by(user_id=owner.id).count() == 0
    if action == "toggle":
        enabled = api_client.post(f"/api/v1/admin/users/{owner.id}/toggle", headers=admin.headers)
        assert enabled.status_code == 200, enabled.text
        assert api_client.get("/api/v1/auth/me", headers=owner.headers).status_code == 401


@pytest.mark.parametrize("token_kind", ["refresh", "expired", "tampered", "no_session"])
def test_invalid_tokens_rejected_by_business_api(api_client, owner, token_kind):
    claims = jwt.decode(owner.token, settings.SECRET_KEY, algorithms=["HS256"])
    secret = settings.SECRET_KEY
    if token_kind == "refresh":
        claims["token_type"] = "refresh"
    elif token_kind == "expired":
        claims["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    elif token_kind == "no_session":
        claims["jti"] = "contract-absent-session"
    else:
        secret = "not-the-app-signing-key-" + "x" * 40
    token = jwt.encode(claims, secret, algorithm="HS256")
    response = api_client.get("/api/v1/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401, response.text


def test_preferences_persist_without_changing_qso_utc(api_client, owner, station_factory, log_factory):
    stn = station_factory(owner)
    qso = log_factory(owner, station_id=stn["id"])
    response = api_client.patch("/api/v1/auth/me", headers=owner.headers,
                                json={"full_name": "Radio Operator", "timezone": "Asia/Shanghai", "language": "en-US"})
    assert response.status_code == 200, response.text
    profile = api_client.get("/api/v1/users/me", headers=owner.headers).json()
    assert {key: profile[key] for key in ("full_name", "timezone", "language")} == {
        "full_name": "Radio Operator", "timezone": "Asia/Shanghai", "language": "en-US",
    }
    saved = api_client.get(f"/api/v1/logs/{qso['id']}", headers=owner.headers).json()
    assert saved["qso_date"] == "2026-01-02"
    assert saved["time_on"] == "12:34:56"
