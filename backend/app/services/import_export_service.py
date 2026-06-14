"""导入导出服务"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.utils.adi_parser import ADIParser
from app.models.qso_log import QSOLog
from app.models.log_file import LogFile
from app.services.log_service import LogService

logger = logging.getLogger("radiomanager.import_export")


class ImportExportService:
    """日志导入导出服务"""

    @staticmethod
    def import_adi(
        db: Session,
        user_id: int,
        file_content: str,
        file_name: str,
        station_id: Optional[int] = None,
    ) -> dict:
        """导入ADI文件"""
        # 解析
        records = ADIParser.parse_adi_file(file_content)
        mapped_records = [ADIParser.map_adi_fields(r) for r in records]

        imported = 0
        skipped = 0
        duplicates = 0
        errors = []

        # 预加载用户现有日志用于去重比对
        # 去重依据: qso_date + call_sign + band（与设计文档要求一致）
        existing_set = set()
        existing_logs = (
            db.query(QSOLog.call_sign, QSOLog.qso_date, QSOLog.band)
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
            )
            .all()
        )
        for row in existing_logs:
            existing_set.add((row.call_sign, str(row.qso_date), row.band))

        for idx, record in enumerate(mapped_records):
            try:
                # 确保必需字段
                if not record.get("call_sign") or not record.get("qso_date"):
                    skipped += 1
                    errors.append({
                        "line": idx + 1,
                        "record": str(record),
                        "error": "Missing required fields (call_sign, qso_date)",
                    })
                    continue

                # 如果没有 station_id，跳过（需要前端传入）
                if not station_id:
                    skipped += 1
                    continue

                # 解析日期
                if isinstance(record.get("qso_date"), str) and len(record["qso_date"]) == 8:
                    qso_date = datetime.strptime(record["qso_date"], "%Y%m%d").date()
                else:
                    qso_date = datetime.strptime(str(record["qso_date"]), "%Y-%m-%d").date()

                call_sign = record.get("call_sign", "").upper()
                band = record.get("band")

                # 去重比对：(call_sign, qso_date, band)
                dedup_key = (call_sign, str(qso_date), band)
                if dedup_key in existing_set:
                    duplicates += 1
                    continue

                # 从schemas创建
                from app.schemas.qso_log import QSOLogCreate
                from decimal import Decimal

                log_data = QSOLogCreate(
                    station_id=station_id,
                    call_sign=call_sign,
                    qso_date=qso_date,
                    time_off=None,
                    band=record.get("band"),
                    freq=Decimal(str(record["freq"])) if record.get("freq") else None,
                    mode=record.get("mode"),
                    rst_sent=record.get("rst_sent"),
                    rst_rcvd=record.get("rst_rcvd"),
                    grid_square=record.get("grid_square"),
                    qsl_sent=record.get("qsl_sent", "N"),
                    qsl_rcvd=record.get("qsl_rcvd", "N"),
                    comment=record.get("comment"),
                )

                LogService.create_log(db, user_id, log_data)
                # 新插入的记录加入去重集合，避免同批导入的重复
                existing_set.add(dedup_key)
                imported += 1

            except Exception as e:
                skipped += 1
                errors.append({
                    "line": idx + 1,
                    "record": str(record),
                    "error": str(e),
                })

        # 记录文件导入历史
        log_file = LogFile(
            user_id=user_id,
            file_name=file_name,
            file_size=len(file_content),
            format="adi",
            qso_count=imported,
            import_status="success" if errors else "partial" if skipped else "success",
            import_error=str(errors) if errors else None,
        )
        db.add(log_file)
        db.commit()

        return {
            "file_id": log_file.id,
            "total_records": len(records),
            "imported": imported,
            "skipped": skipped,
            "duplicates": duplicates,
            "errors": errors[:10],  # 只返回前10个错误
        }

    @staticmethod
    def export_adi(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        band: Optional[str] = None,
        station_id: Optional[int] = None,
    ) -> Tuple[str, str]:
        """导出为ADI格式。返回 (ADI内容, 台站呼号/AllStations)"""
        from app.models.station import Station

        # 确定导出台站呼号
        export_callsign = "AllStations"
        if station_id:
            stn = db.query(Station).filter(Station.id == station_id, Station.is_deleted == False).first()
            if stn:
                export_callsign = stn.callsign

        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False,
        )

        if station_id:
            query = query.filter(QSOLog.station_id == station_id)
        if start_date:
            query = query.filter(QSOLog.qso_date >= start_date)
        if end_date:
            query = query.filter(QSOLog.qso_date <= end_date)
        if band:
            query = query.filter(QSOLog.band == band)

        logs = query.order_by(QSOLog.qso_date).all()

        # 预加载台站信息，减少 N+1 查询
        stations = {s.id: s.callsign for s in db.query(Station).filter(Station.is_deleted == False).all()}

        records = []
        for log in logs:
            station_callsign = stations.get(log.station_id, "")
            record = {
                "station_callsign": station_callsign,
                "call": log.call_sign,
                "qso_date": log.qso_date.strftime("%Y%m%d") if log.qso_date else None,
                "time_on": str(log.time_on) if log.time_on else None,
                "band": log.band,
                "freq": str(log.freq) if log.freq else None,
                "mode": log.mode,
                "rst_sent": log.rst_sent,
                "rst_rcvd": log.rst_rcvd,
                "gridsquare": log.grid_square,
                "qsl_sent": log.qsl_sent,
                "qsl_rcvd": log.qsl_rcvd,
                "comment": log.comment,
            }
            records.append({k: v for k, v in record.items() if v is not None})

        return ADIParser.generate_adi_file(records), export_callsign
