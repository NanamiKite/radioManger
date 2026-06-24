"""回收站服务 - 管理已删除的日志恢复和清理"""

import json
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.qso_log import QSOLog
from app.models.deleted_log import DeletedLog

logger = logging.getLogger("radiomanager.recycle")


class DeletedLogService:
    """回收站服务"""

    # 回收站保留天数
    RETENTION_DAYS = 7

    @staticmethod
    def delete_and_backup(db: Session, qso_log: QSOLog, reason: str = "Station deleted"):
        """删除日志并备份到回收站"""
        # 备份日志数据
        log_data = {
            "user_id": qso_log.user_id,
            "station_id": qso_log.station_id,
            "location_id": qso_log.location_id,
            "call_sign": qso_log.call_sign,
            "qso_date": str(qso_log.qso_date) if qso_log.qso_date else None,
            "qso_date_off": str(qso_log.qso_date_off) if qso_log.qso_date_off else None,
            "time_on": str(qso_log.time_on) if qso_log.time_on else None,
            "time_off": str(qso_log.time_off) if qso_log.time_off else None,
            "band": qso_log.band,
            "band_rx": qso_log.band_rx,
            "freq": str(qso_log.freq) if qso_log.freq else None,
            "freq_rx": str(qso_log.freq_rx) if qso_log.freq_rx else None,
            "mode": qso_log.mode,
            "rst_sent": qso_log.rst_sent,
            "rst_rcvd": qso_log.rst_rcvd,
            "grid_square": qso_log.grid_square,
            "operator": qso_log.operator,
            "qth": qso_log.qth,
            "qsl_sent": qso_log.qsl_sent,
            "qsl_rcvd": qso_log.qsl_rcvd,
            "eqsl_sent": qso_log.eqsl_sent,
            "eqsl_rcvd": qso_log.eqsl_rcvd,
            "lotw_sent": qso_log.lotw_sent,
            "lotw_rcvd": qso_log.lotw_rcvd,
            "distance": qso_log.distance,
            "dxcc": qso_log.dxcc,
            "tx_pwr": qso_log.tx_pwr,
            "my_gridsquare": qso_log.my_gridsquare,
            "station_callsign": qso_log.station_callsign,
            "comment": qso_log.comment,
        }

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        deleted_entry = DeletedLog(
            user_id=qso_log.user_id,
            log_id=qso_log.id,
            log_data=log_data,
            delete_reason=reason,
            deleted_at=now,
            expires_at=now + timedelta(days=DeletedLogService.RETENTION_DAYS),
        )
        db.add(deleted_entry)

        # 标记原日志为已删除
        qso_log.is_deleted = True
        db.flush()

    @staticmethod
    def delete_station_logs(db: Session, user_id: int, station_id: int):
        """删除台站所有日志并移入回收站"""
        logs = (
            db.query(QSOLog)
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.station_id == station_id,
                QSOLog.is_deleted == False,
            )
            .all()
        )
        for log in logs:
            DeletedLogService.delete_and_backup(db, log, f"Station #{station_id} deleted")
        if logs:
            db.commit()
        return len(logs)

    @staticmethod
    def get_deleted_logs(
        db: Session, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple:
        """获取回收站列表"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = (
            db.query(DeletedLog)
            .filter(
                DeletedLog.user_id == user_id,
                DeletedLog.is_restored == False,
                DeletedLog.expires_at > now,
            )
            .order_by(DeletedLog.deleted_at.desc())
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def restore_log(db: Session, deleted_id: int, user_id: int) -> Optional[QSOLog]:
        """从回收站恢复日志"""
        entry = (
            db.query(DeletedLog)
            .filter(
                DeletedLog.id == deleted_id,
                DeletedLog.user_id == user_id,
                DeletedLog.is_restored == False,
            )
            .first()
        )
        if not entry:
            raise ValueError("Deleted log not found or already restored")
        if entry.expires_at and entry.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise ValueError("Deleted log has expired and cannot be restored")

        # 从备份数据恢复
        data = entry.log_data
        new_log = QSOLog(
            user_id=user_id,
            station_id=data.get("station_id"),
            location_id=data.get("location_id"),
            call_sign=data.get("call_sign", ""),
            qso_date=datetime.strptime(data["qso_date"], "%Y-%m-%d").date()
            if isinstance(data.get("qso_date"), str) and len(data["qso_date"]) == 10
            else datetime.strptime(data["qso_date"], "%Y%m%d").date()
            if data.get("qso_date")
            else None,
            qso_date_off=datetime.strptime(data["qso_date_off"], "%Y-%m-%d").date()
            if isinstance(data.get("qso_date_off"), str) and len(data["qso_date_off"]) == 10
            else datetime.strptime(data["qso_date_off"], "%Y%m%d").date()
            if data.get("qso_date_off")
            else None,
            time_on=datetime.strptime(data["time_on"][:8], "%H:%M:%S").time()
            if data.get("time_on") else None,
            time_off=datetime.strptime(data["time_off"][:8], "%H:%M:%S").time()
            if data.get("time_off") else None,
            band=data.get("band"),
            band_rx=data.get("band_rx"),
            freq=Decimal(str(data["freq"])) if data.get("freq") else None,
            freq_rx=Decimal(str(data["freq_rx"])) if data.get("freq_rx") else None,
            mode=data.get("mode"),
            rst_sent=data.get("rst_sent"),
            rst_rcvd=data.get("rst_rcvd"),
            grid_square=data.get("grid_square"),
            operator=data.get("operator"),
            qth=data.get("qth"),
            qsl_sent=data.get("qsl_sent", "N"),
            qsl_rcvd=data.get("qsl_rcvd", "N"),
            eqsl_sent=data.get("eqsl_sent", "N"),
            eqsl_rcvd=data.get("eqsl_rcvd", "N"),
            lotw_sent=data.get("lotw_sent", "N"),
            lotw_rcvd=data.get("lotw_rcvd", "N"),
            distance=data.get("distance"),
            dxcc=data.get("dxcc"),
            tx_pwr=data.get("tx_pwr"),
            my_gridsquare=data.get("my_gridsquare"),
            station_callsign=data.get("station_callsign"),
            comment=data.get("comment"),
        )
        db.add(new_log)
        db.flush()

        # 标记回收站条目为已恢复
        entry.is_restored = True
        db.commit()
        db.refresh(new_log)
        return new_log

    @staticmethod
    def cleanup_expired(db: Session, user_id: Optional[int] = None):
        """清理过期回收站条目"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = db.query(DeletedLog).filter(
            DeletedLog.expires_at <= now,
            DeletedLog.is_restored == False,
        )
        if user_id:
            query = query.filter(DeletedLog.user_id == user_id)

        count = query.count()
        query.delete(synchronize_session=False)
        db.commit()
        if count > 0:
            logger.info(f"Cleaned up {count} expired deleted log entries")
        return count

    @staticmethod
    def batch_permanent_delete(db: Session, deleted_ids: List[int], user_id: int) -> int:
        """批量永久删除回收站条目"""
        entries = (
            db.query(DeletedLog)
            .filter(
                DeletedLog.id.in_(deleted_ids),
                DeletedLog.user_id == user_id,
            )
            .all()
        )

        count = len(entries)
        for entry in entries:
            db.delete(entry)

        db.commit()
        if count > 0:
            logger.info(f"Batch permanently deleted {count} recycle bin entries for user {user_id}")
        return count

    @staticmethod
    def clear_all(db: Session, user_id: int) -> int:
        """清空用户回收站所有条目"""
        count = (
            db.query(DeletedLog)
            .filter(
                DeletedLog.user_id == user_id,
                DeletedLog.is_restored == False,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if count > 0:
            logger.info(f"Cleared {count} recycle bin entries for user {user_id}")
        return count
