from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.station import StationResponse, StationCreate, StationUpdate
from app.services.station_service import StationService
from app.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    station_data: StationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建台站（仅呼号）"""
    try:
        return StationService.create_station(db, current_user.id, station_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[StationResponse])
async def get_stations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取所有台站"""
    return StationService.get_stations(db, current_user.id)


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取单个台站"""
    try:
        return StationService.get_station(db, station_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{station_id}", response_model=StationResponse)
async def update_station(
    station_id: int,
    station_data: StationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新台站呼号"""
    try:
        return StationService.update_station(db, station_id, current_user.id, station_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除台站（需先删除关联日志）"""
    try:
        StationService.delete_station(db, station_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
