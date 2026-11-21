"""导入导出服务"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.utils.adi_parser import ADIParser
from app.models.qso_log import QSOLog
from app.models.log_file import LogFile
from app.models.location import Location
from app.utils.dxcc import lookup_dxcc
from decimal import InvalidOperation
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.qso_log import QSOLogBase
from app.services.station_service import StationService
from app.services.location_service import LocationService
from app.exceptions import ValidationException

logger = logging.getLogger("radiomanager.import_export")

# 批量提交阈值
BATCH_COMMIT_SIZE = 500

# 日期格式列表：(格式字符串, 期望长度)
_DATE_FORMATS = [
    ("%Y-%m-%d", 10),
    ("%Y%m%d", 8),
    ("%d-%m-%y", 8),
    ("%d-%m-%Y", 10),
    ("%y-%m-%d", 8),
    ("%m-%d-%y", 8),
    ("%m-%d-%Y", 10),
]


def _parse_date_flexible(raw: Optional[str]) -> Optional[date]:
    """尝试多种格式解析日期字符串，返回 date 或 None"""
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    for fmt, expected_len in _DATE_FORMATS:
        if len(raw) == expected_len:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    # 最后尝试直接解析前 10 位
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except (ValueError, IndexError):
        return None


def _parse_time_flexible(raw: Optional[str]) -> Optional[time]:
    """尝试解析时间字符串，返回 time 或 None"""
    if not raw:
        return None
    raw = raw.strip()[:8]
    for fmt in ("%H:%M:%S", "%H%M%S", "%H%M", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    return None


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
        """导入ADI文件（支持大量记录，批量提交避免超时）

        去重规则：qso_date + time_on + call_sign + band + mode + freq 六字段一致视为同一条QSO
        合并规则：只填空不覆盖，QSL确认只能 N→Y 不能反向
        """
        if station_id is None:
            active = LocationService.get_active_location(db, user_id)
            if active is None:
                raise ValidationException("No active location. Select a station first.")
            station_id = active.station_id
        StationService.get_station(db, station_id, user_id)
        active_location = LocationService.get_active_location(db, user_id)
        if active_location and active_location.station_id != station_id:
            active_location = None
        if not file_name or len(file_name) > 255:
            raise ValidationException("File name must contain 1 to 255 characters")
        records = ADIParser.parse_adi_file(file_content)

        def key(log):
            return (log.call_sign.upper(), log.qso_date, log.time_on,
                    (log.band or "").lower(), (log.mode or "").upper(),
                    float(log.freq) if log.freq else None)

        existing_map = {
            key(log): log for log in db.query(QSOLog).filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
            ).all()
        }
        counts = {"imported": 0, "duplicates": 0, "merged": 0}
        committed = counts.copy()
        skipped = 0
        errors = []
        pending = 0
        failed = False

        def commit_batch():
            nonlocal pending, committed
            db.commit()
            committed = counts.copy()
            pending = 0

        try:
            for idx, raw in enumerate(records):
                record = ADIParser.map_adi_fields(raw)
                try:
                    record["call_sign"] = record.get("call_sign", "").strip().upper()
                    record["qso_date"] = _parse_date_flexible(record.get("qso_date"))
                    for field in ("qso_date_off",):
                        if record.get(field):
                            parsed = _parse_date_flexible(record[field])
                            if parsed is None:
                                raise ValueError(f"Invalid {field}")
                            record[field] = parsed
                    for field in ("time_on", "time_off"):
                        if record.get(field):
                            parsed = _parse_time_flexible(record[field])
                            if parsed is None:
                                raise ValueError(f"Invalid {field}")
                            record[field] = parsed
                    record["station_id"] = station_id
                    record["location_id"] = active_location.id if active_location else None
                    record["band"] = (record.get("band") or "").lower()
                    record["mode"] = (record.get("mode") or "").upper()
                    if not record.get("my_gridsquare") and active_location:
                        record["my_gridsquare"] = active_location.grid_square
                    data = QSOLogBase.model_validate(record).model_dump()
                except (ValueError, TypeError, InvalidOperation) as exc:
                    skipped += 1
                    errors.append({"line": idx + 1, "error": str(exc)})
                    continue

                candidate = QSOLog(user_id=user_id, **data)
                dedup_key = key(candidate)
                existing = existing_map.get(dedup_key)
                if existing is not None:
                    changed = False
                    for field in ("rst_sent", "rst_rcvd", "grid_square", "my_gridsquare",
                                  "comment", "tx_pwr", "qso_date_off", "time_off"):
                        value = data.get(field)
                        if value and not getattr(existing, field):
                            setattr(existing, field, value)
                            changed = True
                    for received, sent in (("qsl_rcvd", "qsl_sent"),
                                           ("lotw_rcvd", "lotw_sent"),
                                           ("eqsl_rcvd", "eqsl_sent")):
                        if data[received] == "Y" and getattr(existing, received) != "Y":
                            setattr(existing, received, "Y")
                            setattr(existing, sent, "Y")
                            changed = True
                    counts["duplicates"] += 1
                    counts["merged"] += int(changed)
                else:
                    candidate.dxcc = candidate.dxcc or lookup_dxcc(candidate.call_sign)
                    if candidate.qsl_rcvd == "Y":
                        candidate.qsl_sent = candidate.lotw_sent = candidate.lotw_rcvd = "Y"
                        candidate.eqsl_sent = candidate.eqsl_rcvd = "Y"
                    db.add(candidate)
                    existing_map[dedup_key] = candidate
                    counts["imported"] += 1
                    pending += 1
                if pending >= BATCH_COMMIT_SIZE:
                    commit_batch()
            commit_batch()
        except SQLAlchemyError:
            db.rollback()
            failed = True
            counts = committed.copy()
            errors.append({"error": "Database batch failed; current batch rolled back. Earlier batches remain committed."})
            logger.exception("ADI import batch failed for user %s", user_id)

        status = ("partial" if any(committed.values()) else "failed") if failed else ("partial" if errors else "success")
        log_file = LogFile(
            user_id=user_id, file_name=file_name, file_size=len(file_content.encode("utf-8")),
            format="adi", qso_count=counts["imported"], import_status=status,
            import_error=str(errors) if errors else None,
        )
        db.add(log_file)
        db.commit()
        return {"file_id": log_file.id, "total_records": len(records), **counts,
                "updated": counts["merged"], "skipped": skipped,
                "status": status, "database_failed": failed, "errors": errors[:10]}

    @staticmethod
    def export_adi(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        band: Optional[str] = None,
        station_id: Optional[int] = None,
        location_id: Optional[int] = None,
    ) -> Tuple[str, str]:
        """导出为ADI格式（WSJT-X兼容）。返回 (ADI内容, 台站呼号/AllStations)"""
        from app.models.station import Station
        from app.models.location import Location

        export_callsign = "AllStations"
        if station_id is not None:
            stn = StationService.get_station(db, station_id, user_id)
            export_callsign = stn.callsign

        # 查询位置网格（用于 my_gridsquare 过滤）
        location_grid = None
        if location_id is not None:
            loc = LocationService.get_location(db, location_id, user_id)
            if station_id is not None and loc.station_id != station_id:
                raise ValidationException("Location does not belong to the selected station")
            if loc.grid_square:
                location_grid = loc.grid_square.strip()[:4].upper()
                export_callsign = f"{export_callsign}_{location_grid}"

        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id, QSOLog.is_deleted == False,
        )
        if station_id:
            query = query.filter(QSOLog.station_id == station_id)
        if location_id is not None and location_grid:
            query = query.filter(
                func.upper(func.substr(QSOLog.my_gridsquare, 1, 4)) == location_grid
            )
        if start_date:
            query = query.filter(QSOLog.qso_date >= start_date)
        if end_date:
            query = query.filter(QSOLog.qso_date <= end_date)
        if band:
            query = query.filter(QSOLog.band == band)

        logs = query.order_by(QSOLog.qso_date).all()
        station_ids = {log.station_id for log in logs}
        location_ids = {log.location_id for log in logs if log.location_id is not None}
        stations = {s.id: s.callsign for s in db.query(Station.id, Station.callsign).filter(
            Station.user_id == user_id, Station.id.in_(station_ids), Station.is_deleted == False
        ).all()} if station_ids else {}
        locations = {loc.id: loc.grid_square for loc in db.query(Location).join(
            Station, Location.station_id == Station.id
        ).filter(Location.user_id == user_id, Location.id.in_(location_ids),
                 Location.is_deleted == False, Station.user_id == user_id,
                 Station.is_deleted == False).all()} if location_ids else {}

        # ADIF 3.1.0 标准头部
        content = "<ADIF_VER:5>3.1.0 <PROGRAMID:12>RadioManager <PROGRAMVERSION:5>2.5.0 <EOH>\n"
        for log in logs:
            parts = []
            parts.append(f"<call:{len(log.call_sign)}>{log.call_sign}")
            if log.grid_square:
                parts.append(f"<gridsquare:{len(log.grid_square)}>{log.grid_square}")
            if log.mode:
                parts.append(f"<mode:{len(log.mode)}>{log.mode}")
            if log.rst_sent:
                parts.append(f"<rst_sent:{len(log.rst_sent)}>{log.rst_sent}")
            if log.rst_rcvd:
                parts.append(f"<rst_rcvd:{len(log.rst_rcvd)}>{log.rst_rcvd}")
            if log.qso_date:
                ds = log.qso_date.strftime("%Y%m%d")
                parts.append(f"<qso_date:{len(ds)}>{ds}")
            if log.time_on:
                ts = str(log.time_on).replace(":", "")[:6]
                parts.append(f"<time_on:{len(ts)}>{ts}")
            # qso_date_off
            dod = log.qso_date_off or log.qso_date
            if dod:
                ds = dod.strftime("%Y%m%d")
                parts.append(f"<qso_date_off:{len(ds)}>{ds}")
            if log.time_off:
                ts = str(log.time_off).replace(":", "")[:6]
                parts.append(f"<time_off:{len(ts)}>{ts}")
            if log.band:
                parts.append(f"<band:{len(log.band)}>{log.band}")
            if log.band_rx:
                parts.append(f"<band_rx:{len(log.band_rx)}>{log.band_rx}")
            if log.freq:
                fs = str(log.freq)
                parts.append(f"<freq:{len(fs)}>{fs}")
            if log.freq_rx:
                fs = str(log.freq_rx)
                parts.append(f"<freq_rx:{len(fs)}>{fs}")
            # MY_CALL：标准 ADIF 字段，优先用 my_call，其次 station_callsign
            mc = log.my_call or stations.get(log.station_id, "")
            if mc:
                parts.append(f"<my_call:{len(mc)}>{mc}")
            # STATION_CALLSIGN：保留兼容性
            sc = stations.get(log.station_id, "")
            if sc:
                parts.append(f"<station_callsign:{len(sc)}>{sc}")
            # my_gridsquare: 优先使用日志存储的，其次从关联位置获取
            mg = log.my_gridsquare or (locations.get(log.location_id) if log.location_id else None)
            if mg:
                parts.append(f"<my_gridsquare:{len(mg)}>{mg}")
            if log.tx_pwr:
                pw = str(log.tx_pwr)
                parts.append(f"<tx_pwr:{len(pw)}>{pw}")
            # ADIF 3.1.0 扩展字段
            if log.prop_mode:
                parts.append(f"<prop_mode:{len(log.prop_mode)}>{log.prop_mode}")
            if log.sat_name:
                parts.append(f"<sat_name:{len(log.sat_name)}>{log.sat_name}")
            if log.srx:
                parts.append(f"<srx:{len(log.srx)}>{log.srx}")
            if log.stx:
                parts.append(f"<stx:{len(log.stx)}>{log.stx}")
            if log.contest_id:
                parts.append(f"<contest_id:{len(log.contest_id)}>{log.contest_id}")
            for field in ("qsl_sent", "qsl_rcvd", "lotw_sent", "lotw_rcvd", "eqsl_sent", "eqsl_rcvd"):
                value = getattr(log, field)
                if value is not None:
                    parts.append(f"<{field}:{len(value)}>{value}")
            if log.comment:
                parts.append(f"<comment:{len(log.comment)}>{log.comment}")

            content += " ".join(parts) + " <eor>\n"

        return content, export_callsign
