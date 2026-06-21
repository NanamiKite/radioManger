from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.station import Station
from app.models.location import Location
from app.schemas.station import StationCreate, StationUpdate


class StationService:
    """台站服务 - Station 仅为呼号容器，不包含位置信息"""

    @staticmethod
    def create_station(db: Session, user_id: int, station_data: StationCreate) -> Station:
        callsign = station_data.callsign.strip().upper()

        # 检查是否有软删除的同名台站 → 恢复它
        existing = (
            db.query(Station)
            .filter(
                Station.user_id == user_id,
                Station.callsign == callsign,
                Station.is_deleted == True,
            )
            .first()
        )
        if existing:
            existing.is_deleted = False
            from datetime import datetime, timezone
            existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            db.refresh(existing)
            return existing

        db_station = Station(user_id=user_id, callsign=callsign)
        db.add(db_station)
        db.commit()
        db.refresh(db_station)
        return db_station

    @staticmethod
    def get_stations(db: Session, user_id: int) -> List[Station]:
        return (
            db.query(Station)
            .filter(Station.user_id == user_id, Station.is_deleted == False)
            .all()
        )

    @staticmethod
    def get_station(db: Session, station_id: int, user_id: int) -> Station:
        station = (
            db.query(Station)
            .filter(
                Station.id == station_id,
                Station.user_id == user_id,
                Station.is_deleted == False,
            )
            .first()
        )
        if not station:
            raise ValueError("Station not found")
        return station

    @staticmethod
    def update_station(db: Session, station_id: int, user_id: int, station_data: StationUpdate) -> Station:
        db_station = StationService.get_station(db, station_id, user_id)
        update_data = station_data.model_dump(exclude_unset=True)
        if "callsign" in update_data:
            update_data["callsign"] = update_data["callsign"].strip().upper()
        for key, value in update_data.items():
            setattr(db_station, key, value)
        db.commit()
        db.refresh(db_station)
        return db_station

    @staticmethod
    def delete_station(db: Session, station_id: int, user_id: int):
        """删除台站：日志移入回收站，位置和台站软删除"""
        StationService.get_station(db, station_id, user_id)
        stn = db.query(Station).filter(Station.id == station_id).first()

        # 日志移入回收站（7天保留）
        from app.services.deleted_log_service import DeletedLogService
        DeletedLogService.delete_station_logs(db, user_id, station_id)

        # 关联位置软删除
        from app.models.location import Location
        db.query(Location).filter(Location.station_id == station_id).update({"is_deleted": True})

        stn.is_deleted = True
        db.commit()

    @staticmethod
    def get_primary_station(db: Session, user_id: int) -> Optional[Station]:
        """通过激活的 Location 获取当前台站"""
        location = (
            db.query(Location)
            .filter(
                Location.user_id == user_id,
                Location.is_active == True,
                Location.is_deleted == False,
            )
            .first()
        )
        if location:
            return (
                db.query(Station)
                .filter(Station.id == location.station_id, Station.is_deleted == False)
                .first()
            )
        return None
