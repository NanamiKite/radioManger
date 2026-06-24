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


@router.get("/dxcc")
async def get_dxcc_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取DXCC实体排名统计"""
    dxcc_stats = StatsService.get_dxcc_stats(db, current_user.id)
    return {"data": dxcc_stats}


@router.get("/dxcc-chart")
async def get_dxcc_chart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取DXCC图表数据（实体×波段确认状态）"""
    chart = StatsService.get_dxcc_chart(db, current_user.id)
    return {"data": chart}


@router.get("/band-mode-matrix")
async def get_band_mode_matrix(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取波段×模式交叉矩阵"""
    matrix = StatsService.get_band_mode_matrix(db, current_user.id)
    return {"data": matrix}
