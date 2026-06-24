from fastapi import Depends, HTTPException, status, Request
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.utils.security import SecurityUtils
from app.config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """获取当前认证用户"""

    from app.models.user import User

    try:
        # Bearer Token字符串
        token = credentials.credentials

        payload = SecurityUtils.decode_token(token)

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # 服务器模式下检查 token 黑名单
        if jti and settings.DATABASE_MODE == "mysql":
            from app.services.token_blacklist_service import token_blacklist
            if token_blacklist.is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

        user = (
            db.query(User)
            .filter(User.id == int(user_id))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled or deleted"
            )

        # 服务器模式下更新会话活跃时间
        if jti and settings.DATABASE_MODE == "mysql":
            from app.services.session_service import SessionService
            SessionService.update_activity(db, jti)

        return user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
