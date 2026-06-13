from sqlalchemy import Column, Integer, String, Date, Time, Numeric, DateTime, Boolean, ForeignKey, Enum, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

class QSOLog(Base):
    __tablename__ = "qso_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="RESTRICT"), nullable=False)
    
    # 基本通联信息
    call_sign = Column(String(20), nullable=False, index=True)
    qso_date = Column(Date, nullable=False, index=True)
    time_on = Column(Time)
    time_off = Column(Time)
    
    # 频率和模式
    freq = Column(Numeric(10, 6))
    freq_rx = Column(Numeric(10, 6))
    band = Column(String(10), index=True)
    band_rx = Column(String(10))
    mode = Column(String(20), index=True)
    
    # 信号报告
    rst_sent = Column(String(5))
    rst_rcvd = Column(String(5))
    
    # 对方信息
    grid_square = Column(String(6))
    operator = Column(String(50))
    qth = Column(String(200))
    
    # QSL状态
    qsl_sent = Column(Enum("Y", "N", "R", "I", name="qsl_status"), default="N")
    qsl_rcvd = Column(Enum("Y", "N", "R", "I", name="qsl_status"), default="N")
    eqsl_sent = Column(Enum("Y", "N", "R", "I", name="qsl_status"), default="N")
    eqsl_rcvd = Column(Enum("Y", "N", "R", "I", name="qsl_status"), default="N")
    lotw_sent = Column(Enum("Y", "N", name="lotw_status"), default="N")
    lotw_rcvd = Column(Enum("Y", "N", name="lotw_status"), default="N")
    
    # 扩展信息
    distance = Column(Integer)
    comment = Column(Text)
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="qso_logs")
    station = relationship("Station", back_populates="qso_logs")
    
    # 索引
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'qso_date'),
    )
    
    def __repr__(self):
        return f"<QSOLog {self.call_sign} on {self.qso_date}>"
