from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(500))
    role = Column(Enum("user", "admin", name="user_role"), default="user")
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="zh-CN")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    # 账号注销冷却期（服务器模式）
    deletion_scheduled_at = Column(DateTime, nullable=True)   # 申请注销时间，30天后生效
    deletion_cancelled = Column(Boolean, default=False)        # 是否已撤销注销

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    # 关系
    stations = relationship("Station", back_populates="user", cascade="all, delete-orphan")
    qso_logs = relationship("QSOLog", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"
