"""回收站服务 - 管理已删除的日志恢复和清理"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.qso_log import QSOLog
from app.models.deleted_log import DeletedLog
from app.exceptions import NotFoundException, ValidationException

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
            "my_call": qso_log.my_call,
            "comment": qso_log.comment,
            "prop_mode": qso_log.prop_mode,
            "sat_name": qso_log.sat_name,
            "srx": qso_log.srx,
            "stx": qso_log.stx,
            "contest_id": qso_log.contest_id,
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
        """恢复日志；原记录不存在时从已验证的快照重建，不恢复父记录。"""
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
            raise NotFoundException("Deleted log not found or already restored")
        if entry.expires_at and entry.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise ValidationException("Deleted log has expired and cannot be restored")

        # 恢复原记录：将 is_deleted 改回 False
        original_log = db.query(QSOLog).filter(
            QSOLog.id == entry.log_id,
            QSOLog.user_id == user_id,
        ).first()

        from app.services.log_service import LogService
        if original_log is None:
            from app.schemas.qso_log import QSOLogBase
            from app.services.import_export_service import _parse_date_flexible, _parse_time_flexible
            from pydantic import ValidationError
            data = entry.log_data
            if not isinstance(data, dict) or data.get("user_id") != user_id:
                raise ValidationException("Invalid snapshot owner or snapshot data")
            data = data.copy()
            try:
                for field in ("qso_date", "qso_date_off"):
                    raw = data.get(field)
                    if raw is not None:
                        data[field] = _parse_date_flexible(raw)
                        if data[field] is None:
                            raise ValueError(f"Invalid snapshot {field}")
                for field in ("time_on", "time_off"):
                    raw = data.get(field)
                    if raw is not None:
                        data[field] = _parse_time_flexible(raw)
                        if data[field] is None:
                            raise ValueError(f"Invalid snapshot {field}")
                validated = QSOLogBase.model_validate(data)
            except (ValidationError, ValueError, TypeError) as exc:
                raise ValidationException(f"Invalid log snapshot: {exc}") from exc
            LogService.validate_associations(db, user_id, validated.station_id, validated.location_id)
            original_log = QSOLog(user_id=user_id, **validated.model_dump())
            db.add(original_log)
        else:
            LogService.validate_associations(db, user_id, original_log.station_id, original_log.location_id)
        original_log.is_deleted = False

        # 标记回收站条目为已恢复
        entry.is_restored = True
        db.commit()
        db.refresh(original_log)
        return original_log


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
