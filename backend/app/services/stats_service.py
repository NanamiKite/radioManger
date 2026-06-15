"""统计计算服务"""

from sqlalchemy.orm import Session
from sqlalchemy import func
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
        """获取波段统计"""
        rows = (
            db.query(QSOLog.band, func.count(QSOLog.id).label("count"))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.band.isnot(None),
            )
            .group_by(QSOLog.band)
            .all()
        )
        total = sum(r.count for r in rows) or 1
        return [
            {"band": r.band, "qso_count": r.count, "percentage": round(r.count / total * 100, 1)}
            for r in rows
        ]

    @staticmethod
    def get_mode_stats(db: Session, user_id: int) -> list:
        """获取模式统计"""
        rows = (
            db.query(QSOLog.mode, func.count(QSOLog.id).label("count"))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
                QSOLog.mode.isnot(None),
            )
            .group_by(QSOLog.mode)
            .all()
        )
        total = sum(r.count for r in rows) or 1
        return [
            {"mode": r.mode, "qso_count": r.count, "percentage": round(r.count / total * 100, 1)}
            for r in rows
        ]

    @staticmethod
    def get_dxcc_stats(db: Session, user_id: int) -> dict:
        """获取DXCC统计（按呼号前缀分组）"""
        call_signs = (
            db.query(QSOLog.call_sign, func.count(QSOLog.id).label("count"))
            .filter(
                QSOLog.user_id == user_id,
                QSOLog.is_deleted == False,
            )
            .group_by(QSOLog.call_sign)
            .order_by(func.count(QSOLog.id).desc())
            .all()
        )

        dxcc_list = []
        for row in call_signs:
            dxcc_list.append({
                "entity": row.call_sign,
                "code": row.call_sign,
                "count": row.count,
            })

        return {
            "total_dxcc": len(dxcc_list),
            "confirmed_dxcc": 0,
            "dxcc_list": dxcc_list,
        }

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
