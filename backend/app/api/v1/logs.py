from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database.session import get_db
from app.schemas.qso_log import QSOLogResponse, QSOLogCreate, QSOLogUpdate
from app.schemas.common import PaginatedResponse
from app.services.log_service import LogService
from app.dependencies import get_current_user

router = APIRouter()

@router.post("", response_model=QSOLogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_data: QSOLogCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建日志"""
    try:
        log = LogService.create_log(db, current_user.id, log_data)
        return log
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=dict)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    band: Optional[str] = None,
    mode: Optional[str] = None,
    call_sign: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取日志列表"""
    skip = (page - 1) * page_size
    logs, total = LogService.get_logs(
        db, current_user.id,
        skip=skip,
        limit=page_size,
        start_date=start_date,
        end_date=end_date,
        band=band,
        mode=mode,
        call_sign=call_sign
    )
    
    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@router.get("/{log_id}", response_model=QSOLogResponse)
async def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单条日志"""
    try:
        log = LogService.get_log(db, log_id, current_user.id)
        return log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{log_id}", response_model=QSOLogResponse)
async def update_log(
    log_id: int,
    log_data: QSOLogUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新日志"""
    try:
        log = LogService.update_log(db, log_id, current_user.id, log_data)
        return log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除日志"""
    try:
        LogService.delete_log(db, log_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/stats/overview")
async def get_stats_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取统计概览"""
    stats = LogService.get_stats(db, current_user.id)
    return {"data": stats}
