import asyncio
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Request
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.api.v1.auth import ChangePasswordRequest, logout
from app.config import settings
from app.dependencies import authenticate_token, get_current_user
from app.dependencies_admin import get_current_admin
from app.exceptions import AuthException, PermissionException, RadioManagerException
from app.models.user_session import UserSession
from app.schemas.admin import AdminResetPasswordRequest
from app.schemas.user import UserRegister
from app.services.admin_service import AdminService
from app.services.session_service import SessionService
from app.services.user_service import UserService
from app.utils.security import SecurityUtils

PASSWORD = "session-test-password"
NEW_PASSWORD = "replacement-password"


def issue(db, user, *, seconds=3600):
    token, jti = SecurityUtils.create_token({"sub": str(user.id)})
    session = SessionService.create_session(db, user.id, jti, expires_in_seconds=seconds)
    db.commit()
    return token, session


@pytest.mark.parametrize("mode", ["sqlite", "mysql"])
def test_sessions_authoritative_in_both_modes(db, users, monkeypatch, mode):
    monkeypatch.setattr(settings, "DATABASE_MODE", mode)
    user = users[0]
    token, _ = issue(db, user)
    assert authenticate_token(db, token).id == user.id
    SessionService.remove_all_sessions(db, user.id)
    db.commit()
    with pytest.raises(AuthException):
        authenticate_token(db, token)


@pytest.mark.parametrize("claim", ["exp", "sub", "jti", "token_type"])
def test_required_claims(db, users, claim):
    payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=5),
               "sub": str(users[0].id), "jti": "required-claims", "token_type": "access"}
    del payload[claim]
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(AuthException):
        authenticate_token(db, token)


def test_refresh_type_rejected_even_with_matching_session(db, users):
    token, session = issue(db, users[0])
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    payload["token_type"] = "refresh"
    refresh = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(AuthException):
        authenticate_token(db, refresh)
    assert db.query(UserSession).filter_by(token_jti=session.token_jti).count() == 1


def test_missing_expired_and_mismatched_sessions(db, users):
    user, other = users
    token, jti = SecurityUtils.create_token({"sub": str(user.id)})
    with pytest.raises(AuthException):
        authenticate_token(db, token)
    row = SessionService.create_session(db, other.id, jti)
    db.commit()
    with pytest.raises(AuthException):
        authenticate_token(db, token)
    row.user_id = user.id
    row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    db.commit()
    with pytest.raises(AuthException):
        authenticate_token(db, token)


def test_expired_jwt_rejected_with_live_session(db, users):
    token, jti = SecurityUtils.create_token({"sub": str(users[0].id)}, timedelta(seconds=-1))
    SessionService.create_session(db, users[0].id, jti)
    db.commit()
    with pytest.raises(AuthException):
        authenticate_token(db, token)


def test_logout_revokes_only_current_session(db, users):
    token, row = issue(db, users[0])
    second, _ = issue(db, users[0])
    request = Request({"type": "http", "headers": []})
    request.state.auth_jti = row.token_jti
    assert logout(request, db, users[0]) == {"message": "Logout successful"}
    with pytest.raises(AuthException):
        authenticate_token(db, token)
    assert authenticate_token(db, second).id == users[0].id


@pytest.mark.parametrize("operation", ["change", "reset"])
def test_password_mutations_revoke_all_tokens_and_old_password(db, users, operation):
    user = users[0]
    user.password_hash = SecurityUtils.hash_password(PASSWORD)
    db.commit()
    token, _ = issue(db, user)
    second, _ = issue(db, user)
    if operation == "change":
        UserService.change_password(db, user, PASSWORD, NEW_PASSWORD)
    else:
        AdminService.reset_password(db, user.id, NEW_PASSWORD)
    for old_token in (token, second):
        with pytest.raises(AuthException):
            authenticate_token(db, old_token)
    assert UserService.authenticate_user(db, user.username, PASSWORD) is None
    assert UserService.authenticate_user(db, user.username, NEW_PASSWORD).id == user.id


@pytest.mark.parametrize("operation", ["disable", "delete"])
def test_disable_delete_revoke_sessions_permanently(db, users, operation):
    user = users[0]
    token, _ = issue(db, user)
    if operation == "disable":
        AdminService.toggle_user(db, user.id)
    else:
        AdminService.delete_user(db, user.id)
    with pytest.raises(AuthException):
        authenticate_token(db, token)
    user.is_active = True
    user.is_deleted = False
    db.commit()
    with pytest.raises(AuthException):
        authenticate_token(db, token)


@pytest.mark.parametrize("field", ["is_active", "is_deleted"])
def test_live_user_status_is_checked_even_with_session(db, users, field):
    user = users[0]
    token, _ = issue(db, user)
    setattr(user, field, field == "is_deleted")
    db.commit()
    with pytest.raises(AuthException):
        authenticate_token(db, token)


def test_activity_update_is_bounded(db, users):
    token, row = issue(db, users[0])
    before = row.last_active
    authenticate_token(db, token)
    db.refresh(row)
    assert row.last_active == before
    row.last_active = before - timedelta(minutes=2)
    db.commit()
    authenticate_token(db, token)
    db.refresh(row)
    assert row.last_active >= before


def test_revocation_helpers_do_not_commit(db, users):
    _, row = issue(db, users[0])
    jti = row.token_jti
    SessionService.remove_all_sessions(db, users[0].id)
    db.rollback()
    assert db.query(UserSession).filter_by(token_jti=jti).one()
    SessionService.remove_session(db, jti)
    db.rollback()
    assert db.query(UserSession).filter_by(token_jti=jti).one()


@pytest.mark.parametrize("password", ["short", "a" * 73, "界" * 25])
def test_password_limits_match_schema_and_hashing(password):
    with pytest.raises(ValueError):
        SecurityUtils.hash_password(password)
    with pytest.raises(ValidationError):
        UserRegister(username="new-user", email="new@example.com", password=password,
                     confirm_password=password)
    with pytest.raises(ValidationError):
        AdminResetPasswordRequest(new_password=password)
    with pytest.raises(ValidationError):
        ChangePasswordRequest(old_password=PASSWORD, new_password=password, confirm_password=password)


def test_bcrypt_exact_byte_limit():
    password = "界" * 24
    hashed = SecurityUtils.hash_password(password)
    assert SecurityUtils.verify_password(password, hashed)
    assert not SecurityUtils.verify_password(password + "x", hashed)


def test_soft_deleted_registration_conflicts_are_explicit(db, users):
    user = users[0]
    user.is_deleted = True
    db.commit()
    data = UserRegister(username=user.username, email="unused@example.com", password=PASSWORD,
                        confirm_password=PASSWORD)
    with pytest.raises(RadioManagerException) as exc:
        UserService.create_user(db, data)
    assert exc.value.status_code == 409


def test_missing_bearer_is_auth_error(db):
    request = Request({"type": "http", "headers": []})
    with pytest.raises(AuthException):
        get_current_user(request, None, db)


def test_database_failures_are_not_auth_errors(db, users, monkeypatch):
    token, _ = issue(db, users[0])
    def fail(*args, **kwargs):
        raise OperationalError("database unavailable", {}, RuntimeError("offline"))
    monkeypatch.setattr(db, "query", fail)
    with pytest.raises(OperationalError):
        authenticate_token(db, token)


def test_admin_role_required_in_sqlite(users, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_MODE", "sqlite")
    user = users[0]
    user.role = "user"
    with pytest.raises(PermissionException):
        get_current_admin(user)


@pytest.mark.parametrize("message", ["not-json", "[]", "{}", '{"token": 123}', None])
def test_websocket_requires_first_message_token(message):
    from app.dependencies import authenticate_websocket
    class Socket:
        accepted = False
        close_code = None

        async def accept(self):
            self.accepted = True

        async def receive(self):
            return {"type": "websocket.receive", "text": message}

        async def close(self, code):
            self.close_code = code

    socket = Socket()
    assert asyncio.run(authenticate_websocket(socket)) is None
    assert socket.accepted
    assert socket.close_code == 4401


def test_websocket_disconnect_returns_without_close():
    from app.dependencies import authenticate_websocket
    class Socket:
        async def accept(self):
            pass

        async def receive(self):
            return {"type": "websocket.disconnect", "code": 1000}

        async def close(self, code):
            pytest.fail("Disconnected sockets should not be closed again")

    assert asyncio.run(authenticate_websocket(Socket())) is None


@pytest.mark.parametrize("mode", ["sqlite", "mysql"])
def test_realtime_permissions_are_mode_specific(users, monkeypatch, mode):
    from app.dependencies_admin import get_realtime_user
    monkeypatch.setattr(settings, "DATABASE_MODE", mode)
    user = users[0]
    user.role = "user"
    if mode == "mysql":
        with pytest.raises(PermissionException):
            get_realtime_user(user)
    else:
        assert get_realtime_user(user) is user


def test_authentication_does_not_commit_pending_mutations(db, users):
    user = users[0]
    token, row = issue(db, user)
    row.last_active = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=2)
    db.commit()
    original_name = user.full_name
    user.full_name = "uncommitted authentication mutation"
    authenticate_token(db, token)
    db.rollback()
    db.refresh(user)
    assert user.full_name == original_name
