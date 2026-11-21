from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from typing import Optional, Literal
from datetime import date, time, datetime
from decimal import Decimal

QslStatus = Literal["Y", "N", "R", "I"]
LotwStatus = Literal["Y", "N"]

class LogValidation(BaseModel):
    @field_validator("call_sign", mode="before", check_fields=False)
    @classmethod
    def normalize_callsign(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_storage(self):
        limits = {
            "call_sign": 20, "band": 10, "band_rx": 10, "mode": 20,
            "rst_sent": 5, "rst_rcvd": 5, "grid_square": 6, "operator": 50,
            "qth": 200, "dxcc": 100, "my_gridsquare": 6, "station_callsign": 20,
            "my_call": 20, "prop_mode": 20, "sat_name": 50, "srx": 20,
            "stx": 20, "contest_id": 50,
        }
        for field, limit in limits.items():
            value = getattr(self, field, None)
            if value is not None and len(value) > limit:
                raise ValueError(f"{field} must contain at most {limit} characters")
        for field in ("freq", "freq_rx"):
            value = getattr(self, field, None)
            if value is not None and (not value.is_finite() or abs(value) >= 10000):
                raise ValueError(f"{field} is outside Numeric(10, 6) range")
            if value is not None and value.as_tuple().exponent < -6:
                raise ValueError(f"{field} must have at most six decimal places")
        for field in ("distance", "tx_pwr"):
            value = getattr(self, field, None)
            if value is not None and not -2147483648 <= value <= 2147483647:
                raise ValueError(f"{field} is outside integer range")
        for field in ("station_id", "location_id"):
            value = getattr(self, field, None)
            if value is not None and value <= 0:
                raise ValueError(f"{field} must be positive")
        if "call_sign" in self.model_fields_set and not getattr(self, "call_sign", None):
            raise ValueError("call_sign must not be empty")
        return self

class QSOLogBase(LogValidation):
    station_id: int
    location_id: Optional[int] = None
    call_sign: str = Field(..., max_length=20)
    qso_date: date
    qso_date_off: Optional[date] = None
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
    qsl_sent: QslStatus = "N"
    qsl_rcvd: QslStatus = "N"
    eqsl_sent: QslStatus = "N"
    eqsl_rcvd: QslStatus = "N"
    lotw_sent: LotwStatus = "N"
    lotw_rcvd: LotwStatus = "N"
    distance: Optional[int] = None
    dxcc: Optional[str] = None
    tx_pwr: Optional[int] = None
    my_gridsquare: Optional[str] = None
    station_callsign: Optional[str] = None
    comment: Optional[str] = None
    my_call: Optional[str] = None
    prop_mode: Optional[str] = None
    sat_name: Optional[str] = None
    srx: Optional[str] = None
    stx: Optional[str] = None
    contest_id: Optional[str] = None

class QSOLogCreate(QSOLogBase):
    station_id: Optional[int] = None
    location_id: Optional[int] = None
    qso_date: Optional[date] = None  # 未指定时由后端自动填入当前UTC日期
    time_on: Optional[time] = None

class QSOLogUpdate(LogValidation):
    station_id: Optional[int] = None
    call_sign: Optional[str] = None
    location_id: Optional[int] = None
    dxcc: Optional[str] = None
    qso_date: Optional[date] = None
    qso_date_off: Optional[date] = None
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
    qsl_sent: Optional[QslStatus] = None
    qsl_rcvd: Optional[QslStatus] = None
    eqsl_sent: Optional[QslStatus] = None
    eqsl_rcvd: Optional[QslStatus] = None
    lotw_sent: Optional[LotwStatus] = None
    lotw_rcvd: Optional[LotwStatus] = None
    distance: Optional[int] = None
    tx_pwr: Optional[int] = None
    my_gridsquare: Optional[str] = None
    station_callsign: Optional[str] = None
    comment: Optional[str] = None

class QSOLogResponse(QSOLogBase):
    id: int
    user_id: int
    station_callsign: Optional[str] = None
    location_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QSOLogDetail(QSOLogResponse):
    pass
