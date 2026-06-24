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
        """导入ADI文件（支持大量记录，批量提交避免超时）

        去重规则：qso_date + time_on + call_sign + band + mode + freq 六字段一致视为同一条QSO
        合并规则：只填空不覆盖，QSL确认只能 N→Y 不能反向
        """
        from decimal import Decimal

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
        merged = 0
        errors = []
        batch = []

        # 预加载现有日志用于去重（6字段：call_sign + qso_date + time_on + band + mode + freq）
        existing_map: Dict[tuple, QSOLog] = {}
        existing_logs = (
            db.query(QSOLog)
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
            )
            .all()
        )
        for log in existing_logs:
            time_str = log.time_on.strftime("%H%M%S") if log.time_on else ""
            freq_str = str(float(log.freq)) if log.freq else ""
            key = (
                (log.call_sign or "").upper(),
                str(log.qso_date),
                time_str,
                (log.band or "").lower(),
                (log.mode or "").upper(),
                freq_str,
            )
            existing_map[key] = log

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

                # 解析日期（支持多种格式）
                raw_date = str(record.get("qso_date", ""))
                qso_date = None
                date_formats = [
                    ("%Y%m%d", 8),      # 20230523
                    ("%Y-%m-%d", 10),   # 2023-05-23
                    ("%d-%m-%y", 8),    # 23-05-23
                    ("%d-%m-%Y", 10),   # 23-05-2023
                    ("%y-%m-%d", 8),    # 23-05-23
                    ("%m-%d-%y", 8),    # 05-23-23
                    ("%m-%d-%Y", 10),   # 05-23-2023
                ]
                for fmt, expected_len in date_formats:
                    if len(raw_date) == expected_len:
                        try:
                            qso_date = datetime.strptime(raw_date, fmt).date()
                            break
                        except ValueError:
                            continue
                if not qso_date:
                    try:
                        qso_date = datetime.strptime(raw_date, "%Y%m%d").date()
                    except ValueError:
                        raise ValueError(f"Invalid date format: {raw_date}")

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

                # 6字段去重键
                rec_band = (record.get("band") or "").lower()
                rec_mode = (record.get("mode") or "").upper()
                rec_freq = str(float(record["freq"])) if record.get("freq") else ""
                dedup_key = (call_sign, str(qso_date), time_on_str, rec_band, rec_mode, rec_freq)

                existing_log = existing_map.get(dedup_key)

                if existing_log:
                    # === 重复记录：合并逻辑 ===
                    log_changed = False

                    # 1. 只填空不覆盖：导入记录有值但现有记录为空的字段 → 填入
                    fill_fields = [
                        "rst_sent", "rst_rcvd", "grid_square", "my_gridsquare",
                        "comment",
                    ]
                    for field in fill_fields:
                        new_val = record.get(field)
                        if new_val and not getattr(existing_log, field, None):
                            setattr(existing_log, field, new_val)
                            log_changed = True

                    # tx_pwr 需要转为整数
                    if record.get("tx_pwr") and not existing_log.tx_pwr:
                        try:
                            existing_log.tx_pwr = int(record["tx_pwr"])
                            log_changed = True
                        except (ValueError, TypeError):
                            pass

                    # qso_date_off 需要转为 date 对象
                    if record.get("qso_date_off") and not existing_log.qso_date_off:
                        raw_doff = str(record["qso_date_off"])
                        parsed_date_off = None
                        for fmt, expected_len in [("%Y%m%d", 8), ("%Y-%m-%d", 10), ("%d-%m-%y", 8), ("%d-%m-%Y", 10)]:
                            if len(raw_doff) == expected_len:
                                try:
                                    parsed_date_off = datetime.strptime(raw_doff, fmt).date()
                                    break
                                except ValueError:
                                    continue
                        if parsed_date_off:
                            existing_log.qso_date_off = parsed_date_off
                            log_changed = True

                    # time_off 需要转为 time 对象
                    if record.get("time_off") and not existing_log.time_off:
                        raw_toff = record["time_off"].replace(":", "").strip()
                        if len(raw_toff) >= 6:
                            raw_toff = raw_toff[:6]
                        if len(raw_toff) == 6 and raw_toff.isdigit():
                            existing_log.time_off = time(int(raw_toff[0:2]), int(raw_toff[2:4]), int(raw_toff[4:6]))
                            log_changed = True

                    # 2. QSL 确认单向更新（只能 N→Y，不能 Y→N）
                    qsl_fields = [
                        ("qsl_rcvd", "qsl_sent"),
                        ("lotw_rcvd", "lotw_sent"),
                        ("eqsl_rcvd", "eqsl_sent"),
                    ]
                    for rcvd_field, sent_field in qsl_fields:
                        new_val = record.get(rcvd_field, "N")
                        if new_val == "Y" and getattr(existing_log, rcvd_field, "N") != "Y":
                            setattr(existing_log, rcvd_field, "Y")
                            setattr(existing_log, sent_field, "Y")
                            log_changed = True

                    if log_changed:
                        merged += 1

                    duplicates += 1
                    continue

                # === 新记录：直接创建 ===
                my_gridsquare = record.get("my_gridsquare") or record.get("station_callsign_grid") or ""
                if not my_gridsquare and active_location:
                    my_gridsquare = active_location.grid_square or ""

                # 解析 qso_date_off
                qso_date_off_obj = None
                raw_date_off = str(record.get("qso_date_off") or "")
                if raw_date_off:
                    for fmt, expected_len in [("%Y%m%d", 8), ("%Y-%m-%d", 10), ("%d-%m-%y", 8), ("%d-%m-%Y", 10)]:
                        if len(raw_date_off) == expected_len:
                            try:
                                qso_date_off_obj = datetime.strptime(raw_date_off, fmt).date()
                                break
                            except ValueError:
                                continue

                # 解析 time_off
                time_off_obj = None
                raw_time_off = record.get("time_off") or ""
                if raw_time_off:
                    t = raw_time_off.replace(":", "").strip()
                    if len(t) >= 6:
                        t = t[:6]
                    if len(t) == 6 and t.isdigit():
                        time_off_obj = time(int(t[0:2]), int(t[2:4]), int(t[4:6]))

                db_log = QSOLog(
                    user_id=user_id,
                    station_id=station_id,
                    location_id=active_location.id if active_location else None,
                    call_sign=call_sign,
                    qso_date=qso_date,
                    qso_date_off=qso_date_off_obj,
                    dxcc=lookup_dxcc(call_sign),
                    time_on=time_on_obj,
                    time_off=time_off_obj,
                    band=rec_band or "",
                    freq=Decimal(str(record["freq"])) if record.get("freq") else None,
                    mode=record.get("mode"),
                    rst_sent=record.get("rst_sent"),
                    rst_rcvd=record.get("rst_rcvd"),
                    grid_square=record.get("grid_square"),
                    my_gridsquare=my_gridsquare or None,
                    qsl_sent=record.get("qsl_sent", "N"),
                    qsl_rcvd=record.get("qsl_rcvd", "N"),
                    lotw_sent=record.get("lotw_sent", "N"),
                    lotw_rcvd=record.get("lotw_rcvd", "N"),
                    eqsl_sent=record.get("eqsl_sent", "N"),
                    eqsl_rcvd=record.get("eqsl_rcvd", "N"),
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

                # 加入去重集
                existing_map[dedup_key] = db_log
                imported += 1

                # 批量提交，避免事务过大
                if len(batch) >= BATCH_COMMIT_SIZE:
                    db.commit()
                    batch = []

            except Exception as e:
                # 回滚当前事务，避免会话进入错误状态
                db.rollback()
                # 清空待提交批次
                batch = []
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
            "merged": merged,
            "updated": merged,  # 向后兼容
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
        location_id: Optional[int] = None,
    ) -> Tuple[str, str]:
        """导出为ADI格式（WSJT-X兼容）。返回 (ADI内容, 台站呼号/AllStations)"""
        from app.models.station import Station
        from app.models.location import Location

        export_callsign = "AllStations"
        if station_id:
            stn = db.query(Station).filter(Station.id == station_id, Station.user_id == user_id, Station.is_deleted == False).first()
            if stn:
                export_callsign = stn.callsign

        # 查询位置网格（用于 my_gridsquare 过滤）
        location_grid = None
        if location_id:
            loc = db.query(Location).filter(Location.id == location_id, Location.user_id == user_id, Location.is_deleted == False).first()
            if loc and loc.grid_square:
                location_grid = loc.grid_square.strip()[:4].upper()
                export_callsign = f"{export_callsign}_{location_grid}"

        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id, QSOLog.is_deleted == False,
        )
        if station_id:
            query = query.filter(QSOLog.station_id == station_id)
        if location_id and location_grid:
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
        stations = {s.id: s.callsign for s in db.query(Station.id, Station.callsign).filter(Station.user_id == user_id, Station.is_deleted == False).all()}
        # 预加载所有位置网格
        locations = {l.id: l.grid_square for l in db.query(Location).filter(Location.user_id == user_id, Location.is_deleted == False).all()}

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
