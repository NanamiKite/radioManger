from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class LogFile(Base):
    """日志文件追踪表 - 追踪导入的日志文件及其元数据"""
    __tablename__ = "log_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)  # 字节
    file_hash = Column(String(64))  # SHA256

    # 文件信息
    format = Column(String(20))  # adi, adif 等
    qso_count = Column(Integer, default=0)
    import_status = Column(Enum("pending", "success", "failed", "partial", name="import_status"), default="pending")
    import_error = Column(Text)

    # 云备份信息
    github_url = Column(String(500))
    cloud_url = Column(String(500))
    last_sync_at = Column(DateTime)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", backref="log_files")

    __table_args__ = (
        Index("idx_user_hash", "user_id", "file_hash", unique=True),
    )

    def __repr__(self):
        return f"<LogFile {self.file_name}>"
