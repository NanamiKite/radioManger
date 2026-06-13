from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class StationBase(BaseModel):
    callsign: str = Field(..., min_length=3, max_length=20)
    # grid_square: str = Field(..., regex=r'^[A-R]{2}[0-9]{2}([a-x]{2})?$') V1写法，改为pattern
    grid_square: str = Field(..., pattern=r'^[A-R]{2}[0-9]{2}([a-x]{2})?$')
    radio_model: Optional[str] = None
    antenna_model: Optional[str] = None
    antenna_height: Optional[Decimal] = None
    qth: Optional[str] = None
    is_primary: bool = True

class StationCreate(StationBase):
    pass

class StationUpdate(BaseModel):
    radio_model: Optional[str] = None
    antenna_model: Optional[str] = None
    antenna_height: Optional[Decimal] = None
    qth: Optional[str] = None
    is_primary: Optional[bool] = None

class StationResponse(StationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StationDetail(StationResponse):
    pass
