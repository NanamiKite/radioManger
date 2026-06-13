from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.station import Station
from app.schemas.station import StationCreate, StationUpdate

class StationService:
    @staticmethod
    def create_station(db: Session, user_id: int, station_data: StationCreate) -> Station:
        """创建台站"""
        db_station = Station(
            user_id=user_id,
            **station_data.dict()
        )
        db.add(db_station)
        db.commit()
        db.refresh(db_station)
        return db_station
    
    @staticmethod
    def get_stations(db: Session, user_id: int) -> List[Station]:
        """获取用户的所有台站"""
        return db.query(Station).filter(
            Station.user_id == user_id,
            Station.is_deleted == False
        ).all()
    
    @staticmethod
    def get_station(db: Session, station_id: int, user_id: int) -> Station:
        """获取单个台站"""
        station = db.query(Station).filter(
            Station.id == station_id,
            Station.user_id == user_id,
            Station.is_deleted == False
        ).first()
        
        if not station:
            raise ValueError("Station not found")
        
        return station
    
    @staticmethod
    def update_station(db: Session, station_id: int, user_id: int, station_data: StationUpdate) -> Station:
        """更新台站"""
        db_station = StationService.get_station(db, station_id, user_id)
        
        update_data = station_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_station, key, value)
        
        db.commit()
        db.refresh(db_station)
        return db_station
    
    @staticmethod
    def delete_station(db: Session, station_id: int, user_id: int):
        """删除台站"""
        db_station = StationService.get_station(db, station_id, user_id)
        
        # 检查是否存在其他台站
        other_stations = db.query(Station).filter(
            Station.user_id == user_id,
            Station.id != station_id,
            Station.is_deleted == False
        ).count()
        
        if other_stations == 0:
            raise ValueError("Cannot delete the last station")
        
        db_station.is_deleted = True
        db.commit()
    
    @staticmethod
    def get_primary_station(db: Session, user_id: int) -> Optional[Station]:
        """获取主台站"""
        return db.query(Station).filter(
            Station.user_id == user_id,
            Station.is_primary == True,
            Station.is_deleted == False
        ).first()
