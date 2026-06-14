from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.schemas.location import LocationResponse, LocationCreate, LocationUpdate
from app.services.location_service import LocationService
from app.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建位置。首个位置自动激活。"""
    try:
        loc = LocationService.create_location(db, current_user.id, data)
        return _enrich(loc, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[LocationResponse])
async def get_locations(
    station_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取位置列表，可按台站过滤"""
    locs = LocationService.get_locations(db, current_user.id, station_id)
    return [_enrich(l, db) for l in locs]


@router.get("/active/current", response_model=LocationResponse)
async def get_active_location(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前激活的位置"""
    loc = LocationService.get_active_location(db, current_user.id)
    if not loc:
        raise HTTPException(status_code=404, detail="No active location")
    return _enrich(loc, db)


@router.post("/{location_id}/activate", response_model=LocationResponse)
async def activate_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """激活位置（同用户其他位置自动取消激活）"""
    try:
        loc = LocationService.activate_location(db, location_id, current_user.id)
        return _enrich(loc, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新位置信息"""
    try:
        loc = LocationService.update_location(db, location_id, current_user.id, data)
        return _enrich(loc, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除位置"""
    try:
        LocationService.delete_location(db, location_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _enrich(loc, db: Session) -> dict:
    """附加台站呼号"""
    from app.models.station import Station
    stn = db.query(Station.callsign).filter(Station.id == loc.station_id).first()
    data = LocationResponse.model_validate(loc).model_dump()
    data["station_callsign"] = stn.callsign if stn else None
    return data
