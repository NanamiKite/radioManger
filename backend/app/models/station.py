from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Station(Base):
    """台站表 - 仅包含台站标识（呼号），位置的详细信息在 Location 表中"""
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    callsign = Column(String(20), nullable=False, index=True)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="stations")
    qso_logs = relationship("QSOLog", back_populates="station")
    locations = relationship("Location", back_populates="station", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_callsign", "user_id", "callsign", unique=True),
    )

    def __repr__(self):
        return f"<Station {self.callsign}>"
