from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Index, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    callsign = Column(String(20), nullable=False, index=True)
    grid_square = Column(String(6), nullable=False)
    radio_model = Column(String(100))
    antenna_model = Column(String(100))
    antenna_height = Column(Numeric(5, 2))
    qth = Column(String(200))
    
    is_primary = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="stations")
    qso_logs = relationship("QSOLog", back_populates="station")
    
    # 索引
    __table_args__ = (
        Index('idx_user_callsign', 'user_id', 'callsign', unique=True),
    )
    
    def __repr__(self):
        return f"<Station {self.callsign}>"
