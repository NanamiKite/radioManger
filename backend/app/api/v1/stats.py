from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.log_service import LogService
from app.services.stats_service import StatsService
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


@router.get("/band-mode")
async def get_band_mode_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取波段和模式分布统计"""
    band_stats = StatsService.get_band_stats(db, current_user.id)
    mode_stats = StatsService.get_mode_stats(db, current_user.id)
    return {
        "data": {
            "bands": band_stats,
            "modes": mode_stats,
        }
    }
