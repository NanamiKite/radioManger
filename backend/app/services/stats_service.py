"""统计计算服务"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from datetime import date

from app.models.qso_log import QSOLog
from app.models.statistics import Statistics


class StatsService:
    """统计计算服务"""

    @staticmethod
    def get_overview(db: Session, user_id: int) -> dict:
        """获取统计概览"""
        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False,
        )

        total_qso = query.count()

        # DXCC（按dxcc字段去重识别实体数）
        total_dxcc = (
            db.query(func.count(func.distinct(QSOLog.dxcc)))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.dxcc.isnot(None),
                QSOLog.dxcc != "",
            )
            .scalar()
            or 0
        )

        # QSL
        qsl_sent = query.filter(QSOLog.qsl_sent == "Y").count()
        qsl_rcvd = query.filter(QSOLog.qsl_rcvd == "Y").count()
        eqsl_sent = query.filter(QSOLog.eqsl_sent == "Y").count()
        eqsl_rcvd = query.filter(QSOLog.eqsl_rcvd == "Y").count()
        lotw_confirmed = query.filter(QSOLog.lotw_rcvd == "Y").count()

        # 距离
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

        # 最后通联日期
        last_qso = (
            query.order_by(QSOLog.qso_date.desc()).first()
        )

        avg_distance = round(distance_sum / total_qso, 1) if total_qso > 0 else 0

        return {
            "total_qso": total_qso,
            "total_dxcc": total_dxcc,
            "total_waz": 0,  # 需要单独计算
            "qsl_sent": qsl_sent,
            "qsl_rcvd": qsl_rcvd,
            "eqsl_sent": eqsl_sent,
            "eqsl_rcvd": eqsl_rcvd,
            "lotw_confirmed": lotw_confirmed,
            "total_distance": int(distance_sum) if distance_sum else 0,
            "average_distance": avg_distance,
            "last_qso_date": last_qso.qso_date if last_qso else None,
        }

    @staticmethod
    def get_band_stats(db: Session, user_id: int) -> list:
        """获取波段统计（统一小写避免大小写重复）"""
        rows = (
            db.query(func.lower(QSOLog.band).label("band"), func.count(QSOLog.id).label("count"))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.band.isnot(None),
            )
            .group_by(func.lower(QSOLog.band))
            .all()
        )
        total = sum(r.count for r in rows) or 1
        return [
            {"band": r.band, "qso_count": r.count, "percentage": round(r.count / total * 100, 1)}
            for r in rows
        ]

    @staticmethod
    def get_mode_stats(db: Session, user_id: int) -> list:
        """获取模式统计（统一大写显示）"""
        rows = (
            db.query(func.upper(QSOLog.mode).label("mode"), func.count(QSOLog.id).label("count"))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.mode.isnot(None),
            )
            .group_by(func.upper(QSOLog.mode))
            .all()
        )
        total = sum(r.count for r in rows) or 1
        return [
            {"mode": r.mode, "qso_count": r.count, "percentage": round(r.count / total * 100, 1)}
            for r in rows
        ]

    @staticmethod
    def get_dxcc_stats(db: Session, user_id: int) -> dict:
        """获取DXCC统计（按dxcc实体字段分组）"""
        dxcc_entries = (
            db.query(
                QSOLog.dxcc.label("entity"),
                func.count(QSOLog.id).label("count"),
            )
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.dxcc.isnot(None),
                QSOLog.dxcc != "",
            )
            .group_by(QSOLog.dxcc)
            .order_by(func.count(QSOLog.id).desc())
            .all()
        )

        dxcc_list = []
        for row in dxcc_entries:
            dxcc_list.append({
                "entity": row.entity,
                "count": row.count,
            })

        return {
            "total_dxcc": len(dxcc_list),
            "dxcc_list": dxcc_list,
        }

    @staticmethod
    def get_dxcc_chart(db: Session, user_id: int) -> dict:
        """获取DXCC图表数据（实体×波段确认状态）"""
        rows = (
            db.query(
                QSOLog.dxcc.label("entity"),
                func.lower(QSOLog.band).label("band"),
                func.count(QSOLog.id).label("count"),
                func.max(
                    case(
                        (QSOLog.lotw_rcvd == "Y", 1),
                        else_=0,
                    )
                ).label("confirmed"),
            )
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.dxcc.isnot(None),
                QSOLog.dxcc != "",
                QSOLog.band.isnot(None),
            )
            .group_by(QSOLog.dxcc, func.lower(QSOLog.band))
            .all()
        )

        entities = {}
        bands = set()

        for row in rows:
            entity = row.entity
            band = row.band
            bands.add(band)

            if entity not in entities:
                entities[entity] = {}

            entities[entity][band] = {
                "count": row.count,
                "confirmed": bool(row.confirmed),
            }

        entity_totals = {}
        for entity, band_data in entities.items():
            entity_totals[entity] = sum(d["count"] for d in band_data.values())

        sorted_entities = sorted(entity_totals.items(), key=lambda x: x[1], reverse=True)

        band_order = {
            '160m': 1, '80m': 2, '60m': 3, '40m': 4, '30m': 5,
            '20m': 6, '17m': 7, '15m': 8, '12m': 9, '10m': 10,
            '6m': 11, '4m': 12, '2m': 13, '1.25m': 14, '70cm': 15,
            '33cm': 16, '23cm': 17,
        }
        sorted_bands = sorted(bands, key=lambda b: band_order.get(b, 99))

        chart_entities = []
        for entity, total in sorted_entities:
            band_data = entities[entity]
            bands_status = {}
            for band in sorted_bands:
                if band in band_data:
                    bands_status[band] = band_data[band]
                else:
                    bands_status[band] = None

            chart_entities.append({
                "entity": entity,
                "total": total,
                "bands": bands_status,
            })

        band_confirmed = {}
        band_worked = {}
        for band in sorted_bands:
            band_confirmed[band] = 0
            band_worked[band] = 0
            for entity_data in chart_entities:
                bd = entity_data["bands"].get(band)
                if bd:
                    band_worked[band] += 1
                    if bd["confirmed"]:
                        band_confirmed[band] += 1

        return {
            "bands": sorted_bands,
            "entities": chart_entities,
            "band_confirmed": band_confirmed,
            "band_worked": band_worked,
            "total_entities": len(chart_entities),
        }

    @staticmethod
    def get_band_mode_matrix(db: Session, user_id: int) -> list:
        """获取波段×模式交叉矩阵"""
        rows = (
            db.query(
                func.lower(QSOLog.band).label("band"),
                func.upper(QSOLog.mode).label("mode"),
                func.count(QSOLog.id).label("count"),
            )
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.band.isnot(None),
                QSOLog.mode.isnot(None),
            )
            .group_by(func.lower(QSOLog.band), func.upper(QSOLog.mode))
            .order_by(func.lower(QSOLog.band), func.upper(QSOLog.mode))
            .all()
        )

        return [{"band": row.band, "mode": row.mode, "count": row.count} for row in rows]

    @staticmethod
    def refresh_statistics(db: Session, user_id: int):
        """刷新并持久化统计数据"""
        overview = StatsService.get_overview(db, user_id)

        stat = db.query(Statistics).filter(Statistics.user_id == user_id).first()
        if not stat:
            stat = Statistics(user_id=user_id)

        stat.total_qso = overview["total_qso"]
        stat.total_dxcc = overview["total_dxcc"]
        stat.total_waz = overview["total_waz"]
        stat.total_distance = overview["total_distance"]
        stat.qsl_sent = overview["qsl_sent"]
        stat.qsl_rcvd = overview["qsl_rcvd"]
        stat.eqsl_sent = overview["eqsl_sent"]
        stat.eqsl_rcvd = overview["eqsl_rcvd"]
        stat.lotw_confirmed = overview["lotw_confirmed"]

        db.add(stat)
        db.commit()
