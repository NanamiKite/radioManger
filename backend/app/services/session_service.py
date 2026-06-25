"""用户会话追踪服务

仅在 MySQL（服务器）模式下启用。
记录用户登录会话，用于在线用户统计。
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user_session import UserSession
from app.config import settings

logger = logging.getLogger("radiomanager.session")

# 在线判定阈值：15 分钟内有活动视为在线
ONLINE_THRESHOLD_MINUTES = 15


class SessionService:
    """用户会话服务"""

    @staticmethod
    def is_enabled() -> bool:
        """仅 MySQL 模式启用会话追踪"""
        return settings.DATABASE_MODE == "mysql"

    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        jti: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_seconds: int = 604800,  # 7 天
    ) -> Optional[UserSession]:
        """创建会话记录"""
        if not SessionService.is_enabled():
            return None

        session = UserSession(
            user_id=user_id,
            token_jti=jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
                       + timedelta(seconds=expires_in_seconds),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info(f"Session created for user_id={user_id}, jti={jti[:8]}...")
        return session

    @staticmethod
    def remove_session(db: Session, jti: str):
        """移除会话（logout 时调用）"""
        if not SessionService.is_enabled():
            return
        deleted = db.query(UserSession).filter(UserSession.token_jti == jti).delete()
        if deleted:
            db.commit()
            logger.info(f"Session removed, jti={jti[:8]}...")

    @staticmethod
    def remove_all_sessions(db: Session, user_id: int):
        """移除用户所有会话（改密码/重置密码时调用，使所有旧 token 失效）"""
        if not SessionService.is_enabled():
            return
        deleted = db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        if deleted:
            db.commit()
            logger.info(f"All {deleted} sessions removed for user_id={user_id}")

    @staticmethod
    def update_activity(db: Session, jti: str):
        """更新会话活跃时间"""
        if not SessionService.is_enabled():
            return
        session = db.query(UserSession).filter(UserSession.token_jti == jti).first()
        if session:
            session.last_active = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()

    @staticmethod
    def get_online_count(db: Session) -> int:
        """获取在线用户数（15 分钟内活跃）"""
        if not SessionService.is_enabled():
            return 0

        threshold = datetime.now(timezone.utc).replace(tzinfo=None) \
                    - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
        count = db.query(func.count(func.distinct(UserSession.user_id))) \
                  .filter(UserSession.last_active >= threshold) \
                  .scalar()
        return count or 0

    @staticmethod
    def cleanup_expired(db: Session):
        """清理过期会话"""
        if not SessionService.is_enabled():
            return
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        deleted = db.query(UserSession).filter(UserSession.expires_at < now).delete()
        if deleted:
            db.commit()
            logger.info(f"Cleaned up {deleted} expired sessions")
