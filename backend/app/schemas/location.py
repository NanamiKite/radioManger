from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class LocationBase(BaseModel):
    station_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    grid_square: Optional[str] = Field(None, max_length=6)
    radio_model: Optional[str] = Field(None, max_length=100)
    antenna_model: Optional[str] = Field(None, max_length=100)
    antenna_height: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    qth: Optional[str] = Field(None, max_length=200)


class LocationCreate(LocationBase):
    grid_square: str = Field(..., min_length=1, max_length=6)
    name: str = Field("Default", min_length=1, max_length=100)


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    grid_square: Optional[str] = Field(None, min_length=1, max_length=6)
    radio_model: Optional[str] = Field(None, max_length=100)
    antenna_model: Optional[str] = Field(None, max_length=100)
    antenna_height: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    qth: Optional[str] = Field(None, max_length=200)


class LocationResponse(LocationBase):
    id: int
    user_id: int
    is_active: bool
    station_callsign: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
