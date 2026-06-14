from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.database.session import get_db
from app.schemas.qso_log import QSOLogResponse, QSOLogCreate, QSOLogUpdate
from app.schemas.common import PaginatedResponse
from app.services.log_service import LogService
from app.services.import_export_service import ImportExportService
from app.dependencies import get_current_user
from app.models.station import Station

router = APIRouter()


def _enrich_log(log, station_cache: dict) -> dict:
    """为日志填充台站呼号"""
    data = QSOLogResponse.model_validate(log).model_dump()
    data["station_callsign"] = station_cache.get(log.station_id)
    return data


def _build_station_cache(db: Session) -> dict:
    """构建 station_id → callsign 映射"""
    stations = db.query(Station.id, Station.callsign).filter(Station.is_deleted == False).all()
    return {s.id: s.callsign for s in stations}

@router.post("", response_model=QSOLogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_data: QSOLogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建日志。未指定 station_id 时自动使用激活台站"""
    try:
        log = LogService.create_log(db, current_user.id, log_data)
        cache = _build_station_cache(db)
        return _enrich_log(log, cache)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("", response_model=dict)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("qso_date", pattern="^[a-z_]+$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    band: Optional[str] = None,
    mode: Optional[str] = None,
    call_sign: Optional[str] = None,
    station_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取日志列表，支持排序和台站过滤"""
    skip = (page - 1) * page_size
    logs, total = LogService.get_logs(
        db, current_user.id,
        skip=skip, limit=page_size,
        start_date=start_date, end_date=end_date,
        band=band, mode=mode, call_sign=call_sign,
        station_id=station_id,
        sort_by=sort_by, sort_order=sort_order,
    )
    cache = _build_station_cache(db)
    items = [_enrich_log(log, cache) for log in logs]
    return {
        "items": items,
        "total": total, "page": page, "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

# 固定路径路由必须放在 /{log_id} 参数路径之前
@router.get("/stats/overview")
async def get_stats_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取统计概览"""
    stats = LogService.get_stats(db, current_user.id)
    return {"data": stats}


@router.get("/export")
async def export_logs(
    format: str = Query("adi", pattern="^(adi|adif)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    band: Optional[str] = None,
    station_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """导出日志为ADI格式。未指定 station_id 时导出所有台站。"""
    content, callsign = ImportExportService.export_adi(
        db, current_user.id, start_date, end_date, band, station_id
    )
    from datetime import datetime
    date_str = datetime.utcnow().strftime("%Y%m%d")
    callsign_part = callsign if callsign else "AllStations"
    filename = f"{date_str}_{callsign_part}.adi"
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_logs(
    file: UploadFile = File(...),
    station_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """导入ADI文件"""
    if not file.filename or not (file.filename.endswith(".adi") or file.filename.endswith(".adif")):
        raise HTTPException(status_code=400, detail="Only .adi / .adif files are supported")

    content = (await file.read()).decode("utf-8", errors="replace")

    if not station_id:
        from app.services.location_service import LocationService
        active_loc = LocationService.get_active_location(db, current_user.id)
        if active_loc:
            station_id = active_loc.station_id
        else:
            raise HTTPException(status_code=400, detail="No active location. Create and activate a location first.")

    result = ImportExportService.import_adi(db, current_user.id, content, file.filename, station_id)
    return result


@router.get("/{log_id}", response_model=QSOLogResponse)
async def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取单条日志"""
    try:
        log = LogService.get_log(db, log_id, current_user.id)
        cache = _build_station_cache(db)
        return _enrich_log(log, cache)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.patch("/{log_id}", response_model=QSOLogResponse)
async def update_log(
    log_id: int,
    log_data: QSOLogUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新日志"""
    try:
        log = LogService.update_log(db, log_id, current_user.id, log_data)
        cache = _build_station_cache(db)
        return _enrich_log(log, cache)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

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
