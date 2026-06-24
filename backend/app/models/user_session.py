"""用户会话模型 - 用于在线用户统计"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone
from app.database.base import Base


class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_jti = Column(String(100), unique=True, index=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = Column(DateTime)

    def __repr__(self):
        return f"<UserSession user_id={self.user_id}>"
