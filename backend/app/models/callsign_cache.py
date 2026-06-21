from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Index
from datetime import datetime, timezone
from app.database.base import Base

class CallsignCache(Base):
    __tablename__ = "callsign_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    call_sign = Column(String(20), unique=True, nullable=False, index=True)
    
    # 呼号信息
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))
    country = Column(String(100), index=True)
    grid_square = Column(String(6))
    latitude = Column(Numeric(10, 6))
    longitude = Column(Numeric(11, 6))
    class_type = Column(String(50))
    
    # 许可证信息
    license_date = Column(Date)
    license_exp = Column(Date)
    previous_call = Column(String(20))
    
    # 缓存控制
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    qrz_url = Column(String(500))
    
    def __repr__(self):
        return f"<CallsignCache {self.call_sign}>"
