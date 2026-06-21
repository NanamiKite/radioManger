from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from app.database.base import Base


class DeletedLog(Base):
    """删除日志表 - 保存被删除的日志记录用于恢复和审计"""
    __tablename__ = "deleted_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    log_id = Column(Integer)  # 原日志ID

    # 原日志完整数据（JSON格式备份）
    log_data = Column(JSON, nullable=False)

    # 删除信息
    delete_reason = Column(String(500))
    deleted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    expires_at = Column(DateTime)  # 保留过期时间
    is_restored = Column(Boolean, default=False)  # 是否已恢复

    # 关系
    user = relationship("User", backref="deleted_logs")

    __table_args__ = (
        Index("idx_expires_at", "expires_at"),
    )

    def __repr__(self):
        return f"<DeletedLog log_id={self.log_id} by user {self.user_id}>"
