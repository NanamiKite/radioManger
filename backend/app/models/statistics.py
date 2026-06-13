from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey, Index
from datetime import datetime
from app.database.base import Base

class Statistics(Base):
    __tablename__ = "statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 基础统计
    total_qso = Column(Integer, default=0)
    total_dxcc = Column(Integer, default=0)
    total_waz = Column(Integer, default=0)
    total_distance = Column(Integer, default=0)
    
    # QSL统计
    qsl_sent = Column(Integer, default=0)
    qsl_rcvd = Column(Integer, default=0)
    eqsl_sent = Column(Integer, default=0)
    eqsl_rcvd = Column(Integer, default=0)
    lotw_confirmed = Column(Integer, default=0)
    
    # 详细统计数据
    statistic_data = Column(JSON)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_user_id_unique', 'user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<Statistics user_id={self.user_id}>"
