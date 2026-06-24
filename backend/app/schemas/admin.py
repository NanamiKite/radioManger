"""管理后台 Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── 用户管理 ──
class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse]
    total: int
    page: int
    page_size: int


class AdminResetPasswordRequest(BaseModel):
    new_password: str


class AdminUserStatsResponse(BaseModel):
    qso_count: int
    station_count: int


# ── 审计日志 ──
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


# ── 系统配置 ──
class SystemConfigResponse(BaseModel):
    id: int
    key: str
    value: Optional[str] = None
    value_type: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemConfigUpdateRequest(BaseModel):
    key: str
    value: str


class SystemStatusResponse(BaseModel):
    database_mode: str
    total_users: int
    active_users: int
    total_qso: int
    total_stations: int
    online_sessions: int
