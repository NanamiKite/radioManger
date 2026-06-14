from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.station import Station
from app.models.location import Location
from app.schemas.station import StationCreate, StationUpdate


class StationService:
    """台站服务 - Station 仅为呼号容器，不包含位置信息"""

    @staticmethod
    def create_station(db: Session, user_id: int, station_data: StationCreate) -> Station:
        db_station = Station(user_id=user_id, callsign=station_data.callsign.strip().upper())
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
        # 检查是否有日志关联
        from app.models.qso_log import QSOLog
        log_count = (
            db.query(QSOLog)
            .filter(QSOLog.station_id == station_id, QSOLog.is_deleted == False)
            .count()
        )
        if log_count > 0:
            raise ValueError(f"Cannot delete station with {log_count} logs. Delete logs first.")

        StationService.get_station(db, station_id, user_id)
        stn = db.query(Station).filter(Station.id == station_id).first()
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
