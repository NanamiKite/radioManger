from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime


class CallsignQuery(BaseModel):
    """呼号查询请求"""
    call_signs: List[str] = Field(..., max_length=50)


class CallsignInfo(BaseModel):
    """呼号信息响应"""
    call_sign: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    country: Optional[str] = None
    grid_square: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    class_type: Optional[str] = None
    license_date: Optional[date] = None
    license_exp: Optional[date] = None
    previous_call: Optional[str] = None
    qrz_url: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    url: Optional[str] = None
    phone: Optional[str] = None
    cq_zone: Optional[str] = None
    itu_zone: Optional[str] = None
    email: Optional[str] = None
    image: Optional[str] = None
    cached: bool = False
    cached_at: Optional[datetime] = None
    offline: bool = False

    model_config = ConfigDict(from_attributes=True)


class CallsignBatchResponse(BaseModel):
    """批量查询响应"""
    results: List[CallsignInfo]
    found: int
    not_found: int


class CallsignSearchResult(BaseModel):
    """呼号搜索响应"""
    results: List[CallsignInfo]
