"""梅登网格地图 API"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.qso_log import QSOLog
from app.models.location import Location
from app.utils.grid_utils import GridUtils

router = APIRouter()


@router.get("/grids")
async def get_grid_data(
    my_grid: Optional[str] = Query(None, description="按 my_gridsquare 过滤，匹配激活台站网格"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回当前用户 QSO 日志按 4 位网格聚合的数据，用于地图渲染。

    - my_grid: 可选，传入 4 位网格（如 OL63）时仅返回 my_gridsquare 匹配的 QSO
    - 不传 my_grid 时返回该用户所有 QSO 的网格聚合
    """
    user_id = current_user.id

    # 获取激活位置（我的网格）
    active_loc = (
        db.query(Location)
        .filter(
            Location.user_id == user_id,
            Location.is_active == True,
            Location.is_deleted == False,
        )
        .first()
    )

    my_grid_display = None
    my_lat = None
    my_lon = None
    if active_loc and active_loc.grid_square:
        my_grid_display = active_loc.grid_square.strip()[:4].upper()
        pos = GridUtils.to_lat_lon(my_grid_display)
        if pos:
            my_lat, my_lon = pos

    # 基础过滤
    base_filters = [
        QSOLog.user_id == user_id,
        QSOLog.is_deleted == False,
        QSOLog.grid_square.isnot(None),
        QSOLog.grid_square != "",
    ]

    # 按 my_gridsquare 过滤（匹配激活台站网格）
    filter_grid = my_grid or my_grid_display
    if filter_grid:
        # 匹配 my_gridsquare 前 4 位
        base_filters.append(
            func.upper(func.substr(QSOLog.my_gridsquare, 1, 4)) == filter_grid[:4].upper()
        )

    # 按 4 位网格分组聚合
    confirmed_expr = func.sum(
        case(
            (QSOLog.qsl_rcvd == "Y", 1),
            (QSOLog.lotw_rcvd == "Y", 1),
            else_=0,
        )
    )

    rows = (
        db.query(
            QSOLog.grid_square,
            func.count(QSOLog.id).label("count"),
            confirmed_expr.label("confirmed"),
        )
        .filter(*base_filters)
        .group_by(QSOLog.grid_square)
        .all()
    )

    grids = []
    for row in rows:
        raw_grid = (row.grid_square or "").strip().upper()
        if len(raw_grid) < 4:
            continue
        grid4 = raw_grid[:4]
        pos = GridUtils.to_lat_lon(grid4)
        if not pos:
            continue
        lat, lon = pos
        grids.append({
            "grid": grid4,
            "count": row.count,
            "confirmed": int(row.confirmed or 0),
            "lat": lat,
            "lon": lon,
        })

    return {
        "my_grid": my_grid_display,
        "my_lat": my_lat,
        "my_lon": my_lon,
        "grids": grids,
    }
