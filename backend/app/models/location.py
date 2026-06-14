from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Location(Base):
    """台站位置表 - 一个台站可以有多个位置，同一用户只能激活一个位置"""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)

    # 位置标识
    name = Column(String(100), nullable=False)  # 位置名称，如"家里"、"野外"、"移动"
    grid_square = Column(String(6), nullable=False)
    radio_model = Column(String(100))
    antenna_model = Column(String(100))
    antenna_height = Column(Numeric(5, 2))
    qth = Column(String(200))

    # 激活状态：同一用户全局只有一个位置 is_active=True
    is_active = Column(Boolean, default=False)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="locations")
    station = relationship("Station", back_populates="locations")

    def __repr__(self):
        active_flag = " [ACTIVE]" if self.is_active else ""
        return f"<Location {self.name} @ {self.station_id}{active_flag}>"
