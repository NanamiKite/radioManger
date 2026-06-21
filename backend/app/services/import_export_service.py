"""导入导出服务"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, time
from sqlalchemy.orm import Session

from app.utils.adi_parser import ADIParser
from app.models.qso_log import QSOLog
from app.models.log_file import LogFile
from app.models.location import Location
from app.utils.dxcc import lookup_dxcc

logger = logging.getLogger("radiomanager.import_export")

# 批量提交阈值
BATCH_COMMIT_SIZE = 500


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
        """导入ADI文件（支持大量记录，批量提交避免超时）"""
        records = ADIParser.parse_adi_file(file_content)
        mapped_records = [ADIParser.map_adi_fields(r) for r in records]

        # 解析激活位置
        active_location = (
            db.query(Location)
            .filter(
                Location.user_id == user_id,
                Location.is_active == True,
                Location.is_deleted == False,
                Location.station_id == station_id,
            )
            .first()
        ) if station_id else None

        imported = 0
        skipped = 0
        duplicates = 0
        updated = 0
        errors = []
        batch = []

        # 预加载现有日志去重集（呼号+日期+时间 三元组唯一标识一条 QSO）
        existing_set = set()
        existing_logs = (
            db.query(QSOLog.call_sign, QSOLog.qso_date, QSOLog.time_on)
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
            )
            .all()
        )
        for row in existing_logs:
            time_str = row.time_on.strftime("%H%M%S") if row.time_on else ""
            existing_set.add((row.call_sign, str(row.qso_date), time_str))

        for idx, record in enumerate(mapped_records):
            try:
                if not record.get("call_sign") or not record.get("qso_date"):
                    skipped += 1
                    errors.append({
                        "line": idx + 1,
                        "record": str(record),
                        "error": "Missing required fields (call_sign, qso_date)",
                    })
                    continue

                if not station_id:
                    skipped += 1
                    continue

                # 解析日期
                if isinstance(record.get("qso_date"), str) and len(record["qso_date"]) == 8:
                    qso_date = datetime.strptime(record["qso_date"], "%Y%m%d").date()
                else:
                    qso_date = datetime.strptime(str(record["qso_date"]), "%Y-%m-%d").date()

                call_sign = record.get("call_sign", "").upper()

                # 解析 time_on（支持 HHmmss / HH:mm:ss / HHmm 格式）
                time_on_str = ""
                time_on_obj = None
                raw_time = record.get("time_on") or ""
                if raw_time:
                    t = raw_time.replace(":", "").strip()
                    if len(t) >= 6:
                        t = t[:6]
                    elif len(t) == 4:
                        t = t + "00"
                    if len(t) == 6 and t.isdigit():
                        time_on_str = t
                        time_on_obj = time(int(t[0:2]), int(t[2:4]), int(t[4:6]))

                dedup_key = (call_sign, str(qso_date), time_on_str)
                if dedup_key in existing_set:
                    # 重复记录：仅从未确认→确认方向更新 QSL 状态
                    new_qsl_rcvd = record.get("qsl_rcvd", "N")
                    new_lotw_rcvd = record.get("lotw_rcvd", "N")
                    new_eqsl_rcvd = record.get("eqsl_rcvd", "N")
                    has_new_confirm = (new_qsl_rcvd == "Y" or new_lotw_rcvd == "Y" or new_eqsl_rcvd == "Y")
                    if has_new_confirm:
                        existing_log = (
                            db.query(QSOLog)
                            .filter(
                                QSOLog.user_id == user_id,
                                QSOLog.call_sign == call_sign,
                                QSOLog.qso_date == qso_date,
                                QSOLog.is_deleted == False,
                            )
                            .first()
                        )
                        if existing_log:
                            log_updated = False
                            # 仅升级：未确认 → 确认，不降级
                            if new_qsl_rcvd == "Y" and existing_log.qsl_rcvd != "Y":
                                existing_log.qsl_rcvd = "Y"
                                existing_log.qsl_sent = "Y"
                                log_updated = True
                            if new_lotw_rcvd == "Y" and existing_log.lotw_rcvd != "Y":
                                existing_log.lotw_rcvd = "Y"
                                existing_log.lotw_sent = "Y"
                                log_updated = True
                            if new_eqsl_rcvd == "Y" and existing_log.eqsl_rcvd != "Y":
                                existing_log.eqsl_rcvd = "Y"
                                existing_log.eqsl_sent = "Y"
                                log_updated = True
                            if log_updated:
                                updated += 1
                    duplicates += 1
                    continue

                from decimal import Decimal

                # 直接创建模型对象（不通过 LogService.create_log 避免逐条commit）
                # 处理传入的 my_gridsquare/station_callsign
                my_gridsquare = record.get("my_gridsquare") or record.get("station_callsign_grid") or ""
                if not my_gridsquare and active_location:
                    my_gridsquare = active_location.grid_square or ""

                db_log = QSOLog(
                    user_id=user_id,
                    station_id=station_id,
                    location_id=active_location.id if active_location else None,
                    call_sign=call_sign,
                    qso_date=qso_date,
                    dxcc=lookup_dxcc(call_sign),
                    time_on=time_on_obj,
                    time_off=None,
                    band=record.get("band") or "",
                    freq=Decimal(str(record["freq"])) if record.get("freq") else None,
                    mode=record.get("mode"),
                    rst_sent=record.get("rst_sent"),
                    rst_rcvd=record.get("rst_rcvd"),
                    grid_square=record.get("grid_square"),
                    my_gridsquare=my_gridsquare or None,
                    qsl_sent=record.get("qsl_sent", "N"),
                    qsl_rcvd=record.get("qsl_rcvd", "N"),
                    comment=record.get("comment"),
                )

                # QSL/LOTW 联动逻辑：收到即代表已发出
                if db_log.qsl_rcvd == "Y":
                    db_log.qsl_sent = "Y"
                    db_log.lotw_sent = "Y"
                    db_log.lotw_rcvd = "Y"
                    db_log.eqsl_sent = "Y"
                    db_log.eqsl_rcvd = "Y"

                db.add(db_log)
                batch.append(db_log)
                existing_set.add(dedup_key)
                imported += 1

                # 批量提交，避免事务过大
                if len(batch) >= BATCH_COMMIT_SIZE:
                    db.commit()
                    batch = []

            except Exception as e:
                skipped += 1
                errors.append({
                    "line": idx + 1,
                    "record": str(record),
                    "error": str(e),
                })

        # 最后一批提交
        if batch:
            db.commit()
            batch = []

        log_file = LogFile(
            user_id=user_id,
            file_name=file_name,
            file_size=len(file_content),
            format="adi",
            qso_count=imported,
            import_status="success" if not errors else "partial" if skipped else "success",
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
            "updated": updated,
            "errors": errors[:10],
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
        """导出为ADI格式（WSJT-X兼容）。返回 (ADI内容, 台站呼号/AllStations)"""
        from app.models.station import Station
        from app.models.location import Location

        export_callsign = "AllStations"
        if station_id:
            stn = db.query(Station).filter(Station.id == station_id, Station.is_deleted == False).first()
            if stn:
                export_callsign = stn.callsign

        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id, QSOLog.is_deleted == False,
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
        stations = {s.id: s.callsign for s in db.query(Station.id, Station.callsign).filter(Station.is_deleted == False).all()}
        # 预加载所有位置网格
        locations = {l.id: l.grid_square for l in db.query(Location).filter(Location.is_deleted == False).all()}

        # RadioManager 格式导出
        content = "RadioManager ADIF Export<eoh>\n"
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
            if log.freq:
                fs = str(log.freq)
                parts.append(f"<freq:{len(fs)}>{fs}")
            # 台站呼号（从关联表获取）
            sc = stations.get(log.station_id, "")
            if sc:
                parts.append(f"<station_callsign:{len(sc)}>{sc}")
            # my_gridsquare: 优先使用日志存储的，其次从关联位置获取
            mg = log.my_gridsquare or locations.get(log.location_id) if log.location_id else None
            if mg:
                parts.append(f"<my_gridsquare:{len(mg)}>{mg}")
            if log.tx_pwr:
                pw = str(log.tx_pwr)
                parts.append(f"<tx_pwr:{len(pw)}>{pw}")
            if log.comment:
                parts.append(f"<comment:{len(log.comment)}>{log.comment}")

            content += " ".join(parts) + " <eor>\n"

        return content, export_callsign
