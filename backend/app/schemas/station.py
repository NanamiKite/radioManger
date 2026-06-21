from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class StationBase(BaseModel):
    callsign: str = Field(..., min_length=3, max_length=20)


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    callsign: Optional[str] = None


class StationResponse(StationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
