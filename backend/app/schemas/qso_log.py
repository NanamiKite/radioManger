from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime
from decimal import Decimal

class QSOLogBase(BaseModel):
    station_id: int
    call_sign: str = Field(..., max_length=20)
    qso_date: date
    time_on: Optional[time] = None
    time_off: Optional[time] = None
    freq: Optional[Decimal] = None
    freq_rx: Optional[Decimal] = None
    band: Optional[str] = None
    band_rx: Optional[str] = None
    mode: Optional[str] = None
    rst_sent: Optional[str] = None
    rst_rcvd: Optional[str] = None
    grid_square: Optional[str] = None
    operator: Optional[str] = None
    qth: Optional[str] = None
    qsl_sent: Optional[str] = "N"
    qsl_rcvd: Optional[str] = "N"
    eqsl_sent: Optional[str] = "N"
    eqsl_rcvd: Optional[str] = "N"
    lotw_sent: Optional[str] = "N"
    lotw_rcvd: Optional[str] = "N"
    distance: Optional[int] = None
    dxcc: Optional[str] = None         # DXCC实体（自动从呼号推断，可手动修改）
    comment: Optional[str] = None

class QSOLogCreate(QSOLogBase):
    station_id: Optional[int] = None  # 未指定时由 LogService 自动填入激活台站

class QSOLogUpdate(BaseModel):
    call_sign: Optional[str] = None
    dxcc: Optional[str] = None
    qso_date: Optional[date] = None
    time_on: Optional[time] = None
    time_off: Optional[time] = None
    freq: Optional[Decimal] = None
    freq_rx: Optional[Decimal] = None
    band: Optional[str] = None
    band_rx: Optional[str] = None
    mode: Optional[str] = None
    rst_sent: Optional[str] = None
    rst_rcvd: Optional[str] = None
    grid_square: Optional[str] = None
    operator: Optional[str] = None
    qth: Optional[str] = None
    qsl_sent: Optional[str] = None
    qsl_rcvd: Optional[str] = None
    eqsl_sent: Optional[str] = None
    eqsl_rcvd: Optional[str] = None
    lotw_sent: Optional[str] = None
    lotw_rcvd: Optional[str] = None
    distance: Optional[int] = None
    comment: Optional[str] = None

class QSOLogResponse(QSOLogBase):
    id: int
    user_id: int
    station_callsign: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QSOLogDetail(QSOLogResponse):
    pass
