"""管理后台 API - 仅服务器模式（MySQL）启用"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.dependencies_admin import get_current_admin
from app.models.user import User
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService
from app.services.config_service import ConfigService
from app.schemas.admin import (
    AdminUserResponse, AdminUserListResponse, AdminResetPasswordRequest,
    AdminUserStatsResponse, AuditLogResponse, AuditLogListResponse,
    SystemConfigResponse, SystemConfigUpdateRequest, SystemStatusResponse,
)
from app.config import settings

router = APIRouter()


# ── 用户管理 ──
@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取用户列表"""
    skip = (page - 1) * page_size
    items, total = AdminService.get_users(db, keyword=keyword, role=role, is_active=is_active, skip=skip, limit=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取用户详情"""
    user = AdminService.get_user_detail(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/toggle", response_model=AdminUserResponse)
async def toggle_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """启用/禁用用户"""
    user = AdminService.toggle_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    AuditService.log(db, current_user, "ADMIN_TOGGLE_USER", "user", user_id,
                     detail=f"{'enabled' if user.is_active else 'disabled'} user {user.username}",
                     ip_address=request.client.host if request.client else None)
    return user


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    body: AdminResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """重置用户密码"""
    user = AdminService.reset_password(db, user_id, body.new_password)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    AuditService.log(db, current_user, "ADMIN_RESET_PASSWORD", "user", user_id,
                     detail=f"Reset password for user {user.username}",
                     ip_address=request.client.host if request.client else None)
    return {"message": "Password reset successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = AdminService.delete_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    AuditService.log(db, current_user, "ADMIN_DELETE_USER", "user", user_id,
                     ip_address=request.client.host if request.client else None)
    return {"message": "User deleted"}


@router.get("/users/{user_id}/stats", response_model=AdminUserStatsResponse)
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取用户统计摘要"""
    return AdminService.get_user_stats(db, user_id)


# ── 审计日志 ──
@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取审计日志"""
    skip = (page - 1) * page_size
    items, total = AuditService.get_logs(db, user_id=user_id, action=action, skip=skip, limit=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── 系统配置 ──
@router.get("/system/config")
async def get_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取所有系统配置"""
    return ConfigService.get_all(db)


@router.patch("/system/config")
async def update_config(
    body: SystemConfigUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """更新系统配置"""
    config = ConfigService.update(db, body.key, body.value, current_user.id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    AuditService.log(db, current_user, "ADMIN_UPDATE_CONFIG", "system", None,
                     detail=f"{body.key} = {body.value}",
                     ip_address=request.client.host if request.client else None)
    return {"message": "Config updated", "key": body.key, "value": body.value}


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """获取系统状态"""
    from sqlalchemy import func
    total_users = db.query(func.count(User.id)).filter(User.is_deleted == False).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_deleted == False, User.is_active == True).scalar() or 0
    from app.models.qso_log import QSOLog
    from app.models.station import Station
    total_qso = db.query(func.count(QSOLog.id)).filter(QSOLog.is_deleted == False).scalar() or 0
    total_stations = db.query(func.count(Station.id)).filter(Station.is_deleted == False).scalar() or 0
    from app.models.user_session import UserSession
    online_sessions = db.query(func.count(UserSession.id)).scalar() or 0

    return {
        "database_mode": settings.DATABASE_MODE,
        "total_users": total_users,
        "active_users": active_users,
        "total_qso": total_qso,
        "total_stations": total_stations,
        "online_sessions": online_sessions,
    }
