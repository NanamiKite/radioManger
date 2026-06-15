from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.log_service import LogService
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/overview")
async def get_overview(
    station_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取统计概览。可指定 station_id 仅统计该台站"""
    stats = LogService.get_stats(db, current_user.id, station_id)
    return {"data": stats}
