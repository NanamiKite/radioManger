import asyncio
import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.session import get_db, SessionLocal
from app.exceptions import AuthException
from app.models.user import User
from app.models.user_session import UserSession
from app.services.session_service import ACTIVITY_UPDATE_SECONDS, SessionService
from app.utils.security import InvalidTokenError, SecurityUtils, TokenExpiredError

security = HTTPBearer(auto_error=False)


def _authenticate_token(db: Session, token: str) -> tuple[User, str, bool]:
    """Validate once and stage bounded activity updates without committing."""
    try:
        payload = SecurityUtils.decode_token(token)
    except (InvalidTokenError, TokenExpiredError) as exc:
        raise AuthException(str(exc)) from exc

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = db.query(User).filter(User.id == int(payload["sub"])).populate_existing().first()
    if not user or user.is_deleted or not user.is_active:
        raise AuthException("Account is disabled, deleted, or missing")
    session = db.query(UserSession).filter(
        UserSession.token_jti == payload["jti"],
        UserSession.user_id == user.id,
        UserSession.expires_at > now,
    ).populate_existing().first()
    if session is None:
        raise AuthException("Session expired or revoked")
    activity_updated = False
    if session.last_active is None or session.last_active <= now - timedelta(seconds=ACTIVITY_UPDATE_SECONDS):
        activity_updated = SessionService.update_activity(db, payload["jti"])
    return user, payload["jti"], activity_updated


def authenticate_token(db: Session, token: str) -> User:
    """Authenticate in the caller's transaction; never commit caller mutations."""
    user, _, _ = _authenticate_token(db, token)
    return user


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthException("Bearer token required")
    user, jti, activity_updated = _authenticate_token(db, credentials.credentials)
    request.state.auth_jti = jti
    # This dependency owns the read-only HTTP authentication transaction.
    if activity_updated:
        db.commit()
    return user


def authenticate_websocket_token(token: str) -> User:
    """Return a fully loaded, detached user without retaining a database session."""
    with SessionLocal() as db:
        user, _, activity_updated = _authenticate_token(db, token)
        if activity_updated:
            db.commit()
            db.refresh(user)
        db.expunge(user)
        return user


async def authenticate_websocket(ws: WebSocket) -> tuple[str, User] | None:
    """Accept a connection and require a first-message access token within five seconds."""
    await ws.accept()
    try:
        event = await asyncio.wait_for(ws.receive(), timeout=5)
        if event["type"] == "websocket.disconnect":
            return None
        text = event.get("text")
        if not isinstance(text, str):
            await ws.close(code=4401)
            return None
        message = json.loads(text)
        if not isinstance(message, dict) or not isinstance(message.get("token"), str) or not message["token"]:
            await ws.close(code=4401)
            return None
        token = message["token"]
        user = await run_in_threadpool(authenticate_websocket_token, token)
        return token, user
    except WebSocketDisconnect:
        return None
    except (asyncio.TimeoutError, json.JSONDecodeError, UnicodeDecodeError, AuthException):
        try:
            await ws.close(code=4401)
        except WebSocketDisconnect:
            pass
        return None
