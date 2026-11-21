"""Persistent login sessions and revocation for SQLite and MySQL."""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user_session import UserSession

logger = logging.getLogger("radiomanager.session")

# 在线判定阈值：15 分钟内有活动视为在线
ONLINE_THRESHOLD_MINUTES = 15
ACTIVITY_UPDATE_SECONDS = 60


class SessionService:
    """用户会话服务"""

    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        jti: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_seconds: int = 604800,  # 7 天
    ) -> UserSession:
        """创建会话记录"""
        session = UserSession(
            user_id=user_id,
            token_jti=jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
                       + timedelta(seconds=expires_in_seconds),
        )
        db.add(session)
        db.flush()
        return session

    @staticmethod
    def remove_session(db: Session, jti: str):
        """移除会话（logout 时调用）"""
        deleted = db.query(UserSession).filter(UserSession.token_jti == jti).delete()
        if deleted:
            db.flush()
            logger.info(f"Session removed, jti={jti[:8]}...")

    @staticmethod
    def remove_all_sessions(db: Session, user_id: int):
        """移除用户所有会话（改密码/重置密码时调用，使所有旧 token 失效）"""
        deleted = db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        if deleted:
            db.flush()
            logger.info(f"All {deleted} sessions removed for user_id={user_id}")

    @staticmethod
    def update_activity(db: Session, jti: str) -> bool:
        """Stage a bounded activity update; the caller owns the transaction."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        threshold = now - timedelta(seconds=ACTIVITY_UPDATE_SECONDS)
        updated = db.query(UserSession).filter(
            UserSession.token_jti == jti,
            (UserSession.last_active <= threshold) | UserSession.last_active.is_(None),
        ).update({UserSession.last_active: now}, synchronize_session=False)
        return bool(updated)

    @staticmethod
    def get_online_count(db: Session) -> int:
        """获取在线用户数（15 分钟内活跃）"""
        threshold = datetime.now(timezone.utc).replace(tzinfo=None) \
                    - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
        count = db.query(func.count(func.distinct(UserSession.user_id))) \
                  .filter(UserSession.last_active >= threshold,
                          UserSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)) \
                  .scalar()
        return count or 0

    @staticmethod
    def cleanup_expired(db: Session):
        """清理过期会话"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        deleted = db.query(UserSession).filter(UserSession.expires_at < now).delete()
        if deleted:
            db.commit()
            logger.info(f"Cleaned up {deleted} expired sessions")
