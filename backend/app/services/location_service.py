from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.location import Location
from app.models.station import Station
from app.schemas.location import LocationCreate, LocationUpdate


class LocationService:
    """位置服务 - 一个台站可以有多个位置，全局只能激活一个位置"""

    @staticmethod
    def _deactivate_all(db: Session, user_id: int):
        """将用户所有位置取消激活"""
        db.query(Location).filter(Location.user_id == user_id).update(
            {"is_active": False}
        )

    @staticmethod
    def create_location(db: Session, user_id: int, data: LocationCreate) -> Location:
        """创建位置。如果是用户的第一个位置则自动激活（全局），否则不激活。"""
        total_existing = (
            db.query(Location)
            .filter(Location.user_id == user_id, Location.is_deleted == False)
            .count()
        )
        is_first = total_existing == 0

        loc = Location(
            user_id=user_id,
            station_id=data.station_id,
            name=data.name,
            grid_square=data.grid_square.strip().upper(),
            radio_model=data.radio_model,
            antenna_model=data.antenna_model,
            antenna_height=data.antenna_height,
            qth=data.qth,
            is_active=is_first,
        )
        if is_first:
            LocationService._deactivate_all(db, user_id)
            loc.is_active = True

        db.add(loc)
        db.commit()
        db.refresh(loc)
        return loc

    @staticmethod
    def get_locations(db: Session, user_id: int, station_id: Optional[int] = None) -> List[Location]:
        """获取用户的位置列表，可按台站过滤"""
        query = db.query(Location).filter(
            Location.user_id == user_id, Location.is_deleted == False
        )
        if station_id:
            query = query.filter(Location.station_id == station_id)
        return query.order_by(Location.station_id, Location.created_at).all()

    @staticmethod
    def get_location(db: Session, location_id: int, user_id: int) -> Location:
        loc = (
            db.query(Location)
            .filter(
                Location.id == location_id,
                Location.user_id == user_id,
                Location.is_deleted == False,
            )
            .first()
        )
        if not loc:
            raise ValueError("Location not found")
        return loc

    @staticmethod
    def update_location(db: Session, location_id: int, user_id: int, data: LocationUpdate) -> Location:
        db_loc = LocationService.get_location(db, location_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_loc, key, value)
        db.commit()
        db.refresh(db_loc)
        return db_loc

    @staticmethod
    def activate_location(db: Session, location_id: int, user_id: int) -> Location:
        """激活一个位置，取消用户所有其他位置的激活状态"""
        target = LocationService.get_location(db, location_id, user_id)
        LocationService._deactivate_all(db, user_id)
        target.is_active = True
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def delete_location(db: Session, location_id: int, user_id: int):
        db_loc = LocationService.get_location(db, location_id, user_id)
        db_loc.is_deleted = True
        db.commit()

    @staticmethod
    def get_active_location(db: Session, user_id: int) -> Optional[Location]:
        """获取用户当前激活的位置"""
        return (
            db.query(Location)
            .filter(
                Location.user_id == user_id,
                Location.is_active == True,
                Location.is_deleted == False,
            )
            .first()
        )

    @staticmethod
    def get_locations_with_station(db: Session, user_id: int) -> List[dict]:
        """获取位置列表，每个位置附带台站呼号"""
        results = (
            db.query(Location, Station.callsign)
            .join(Station, Location.station_id == Station.id)
            .filter(
                Location.user_id == user_id,
                Location.is_deleted == False,
                Station.is_deleted == False,
            )
            .order_by(Station.callsign, Location.created_at)
            .all()
        )
        out = []
        for loc, csign in results:
            d = {
                "id": loc.id,
                "user_id": loc.user_id,
                "station_id": loc.station_id,
                "name": loc.name,
                "station_callsign": csign,
                "grid_square": loc.grid_square,
                "radio_model": loc.radio_model,
                "antenna_model": loc.antenna_model,
                "antenna_height": float(loc.antenna_height) if loc.antenna_height else None,
                "qth": loc.qth,
                "is_active": loc.is_active,
                "is_deleted": loc.is_deleted,
                "created_at": loc.created_at,
                "updated_at": loc.updated_at,
            }
            out.append(d)
        return out
