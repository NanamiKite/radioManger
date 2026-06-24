"""系统配置模型 - 管理员可配置的系统参数"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from app.database.base import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String(20), default="string")
    description = Column(String(200))
    updated_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
                        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value}>"
