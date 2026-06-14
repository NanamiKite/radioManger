from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.models.qso_log import QSOLog
from app.models.location import Location
from app.schemas.qso_log import QSOLogCreate, QSOLogUpdate
from app.services.station_service import StationService
from app.utils.dxcc import lookup_dxcc


# 允许排序的安全字段白名单
SORTABLE_FIELDS = {
    "qso_date", "call_sign", "band", "mode", "freq",
    "rst_sent", "rst_rcvd", "qsl_sent", "qsl_rcvd",
    "dxcc", "distance", "created_at", "station_id",
}


class LogService:
    @staticmethod
    def create_log(db: Session, user_id: int, log_data: QSOLogCreate) -> QSOLog:
        """创建日志。自动推断DXCC。未指定station_id时使用激活台站。"""
        data = log_data.model_dump()

        if not data.get("station_id"):
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
                data["station_id"] = location.station_id
            else:
                raise ValueError(
                    "No active location. Please create a location and activate it first."
                )

        if "call_sign" in data and data["call_sign"]:
            cs = data["call_sign"].strip().upper()
            data["call_sign"] = cs
            # 自动推断DXCC（用户未手动指定时）
            if not data.get("dxcc"):
                data["dxcc"] = lookup_dxcc(cs)

        db_log = QSOLog(user_id=user_id, **data)
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    @staticmethod
    def get_logs(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        band: Optional[str] = None,
        mode: Optional[str] = None,
        call_sign: Optional[str] = None,
        station_id: Optional[int] = None,
        sort_by: str = "qso_date",
        sort_order: str = "desc",
    ) -> tuple[List[QSOLog], int]:
        """获取日志列表，支持排序"""
        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id, QSOLog.is_deleted == False
        )

        if station_id:
            query = query.filter(QSOLog.station_id == station_id)
        if start_date:
            query = query.filter(QSOLog.qso_date >= start_date)
        if end_date:
            query = query.filter(QSOLog.qso_date <= end_date)
        if band:
            query = query.filter(QSOLog.band == band)
        if mode:
            query = query.filter(QSOLog.mode == mode)
        if call_sign:
            query = query.filter(QSOLog.call_sign.ilike(f"%{call_sign}%"))

        # 安全排序
        sort_col = getattr(QSOLog, sort_by, None) if sort_by in SORTABLE_FIELDS else QSOLog.qso_date
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total

    @staticmethod
    def get_log(db: Session, log_id: int, user_id: int) -> QSOLog:
        log = (
            db.query(QSOLog)
            .filter(
                QSOLog.id == log_id,
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
            )
            .first()
        )
        if not log:
            raise ValueError("Log not found")
        return log

    @staticmethod
    def update_log(
        db: Session, log_id: int, user_id: int, log_data: QSOLogUpdate
    ) -> QSOLog:
        db_log = LogService.get_log(db, log_id, user_id)
        update_data = log_data.model_dump(exclude_unset=True)
        if "call_sign" in update_data and update_data["call_sign"]:
            update_data["call_sign"] = update_data["call_sign"].strip().upper()
        for key, value in update_data.items():
            setattr(db_log, key, value)
        db.commit()
        db.refresh(db_log)
        return db_log

    @staticmethod
    def delete_log(db: Session, log_id: int, user_id: int):
        db_log = LogService.get_log(db, log_id, user_id)
        db_log.is_deleted = True
        db.commit()

    @staticmethod
    def get_stats(db: Session, user_id: int) -> dict:
        from sqlalchemy import func

        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id, QSOLog.is_deleted == False
        )
        total_qso = query.count()

        total_dxcc = (
            db.query(func.count(func.distinct(QSOLog.call_sign)))
            .filter(QSOLog.user_id == user_id, QSOLog.is_deleted == False)
            .scalar()
            or 0
        )

        qsl_sent = query.filter(QSOLog.qsl_sent == "Y").count()
        qsl_rcvd = query.filter(QSOLog.qsl_rcvd == "Y").count()
        eqsl_sent = query.filter(QSOLog.eqsl_sent == "Y").count()
        eqsl_rcvd = query.filter(QSOLog.eqsl_rcvd == "Y").count()
        lotw_confirmed = query.filter(QSOLog.lotw_rcvd == "Y").count()

        distance_sum = (
            db.query(func.sum(QSOLog.distance))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.distance.isnot(None),
            )
            .scalar()
            or 0
        )

        return {
            "total_qso": total_qso,
            "total_dxcc": total_dxcc or 0,
            "qsl_sent": qsl_sent,
            "qsl_rcvd": qsl_rcvd,
            "eqsl_sent": eqsl_sent,
            "eqsl_rcvd": eqsl_rcvd,
            "lotw_confirmed": lotw_confirmed,
            "total_distance": int(distance_sum) if distance_sum else 0,
        }
