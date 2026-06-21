from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class LocationBase(BaseModel):
    station_id: int
    name: str = Field(..., min_length=1, max_length=100)
    grid_square: Optional[str] = None
    radio_model: Optional[str] = None
    antenna_model: Optional[str] = None
    antenna_height: Optional[Decimal] = None
    qth: Optional[str] = None


class LocationCreate(LocationBase):
    grid_square: str = Field(...)
    name: str = Field("Default", min_length=1, max_length=100)


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    grid_square: Optional[str] = None
    radio_model: Optional[str] = None
    antenna_model: Optional[str] = None
    antenna_height: Optional[Decimal] = None
    qth: Optional[str] = None


class LocationResponse(LocationBase):
    id: int
    user_id: int
    is_active: bool
    station_callsign: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
