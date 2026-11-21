from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime


class StationBase(BaseModel):
    callsign: str = Field(..., min_length=3, max_length=20)

    @field_validator("callsign", mode="before")
    @classmethod
    def normalize_callsign(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    callsign: Optional[str] = Field(None, min_length=3, max_length=20)

    @field_validator("callsign", mode="before")
    @classmethod
    def normalize_callsign(cls, value):
        if value is None:
            raise ValueError("callsign cannot be null")
        return value.strip().upper() if isinstance(value, str) else value


class StationResponse(StationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
