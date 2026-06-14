from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class SyncHistory(Base):
    """同步历史表 - 记录与GitHub或云服务的同步操作"""
    __tablename__ = "sync_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 同步信息
    sync_type = Column(Enum("push", "pull", "merge", name="sync_type"))
    source = Column(String(50))  # github, cloud
    status = Column(Enum("pending", "success", "failed", name="sync_status"), default="pending")

    # 操作统计
    added_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    deleted_count = Column(Integer, default=0)
    conflict_count = Column(Integer, default=0)

    # 错误信息
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)

    # 关系
    user = relationship("User", backref="sync_history")

    def __repr__(self):
        return f"<SyncHistory {self.sync_type} by user {self.user_id}>"
