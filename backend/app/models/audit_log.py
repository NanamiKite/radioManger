"""审计日志模型 - 记录用户操作（不记录QSO内容）"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from app.database.base import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50))
    target_id = Column(Integer)
    detail = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)

    def __repr__(self):
        return f"<AuditLog {self.username} {self.action} at {self.created_at}>"
