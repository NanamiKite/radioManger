from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date
from app.models.qso_log import QSOLog
from app.schemas.qso_log import QSOLogCreate, QSOLogUpdate

class LogService:
    @staticmethod
    def create_log(db: Session, user_id: int, log_data: QSOLogCreate) -> QSOLog:
        """创建日志"""
        db_log = QSOLog(
            user_id=user_id,
            # **log_data.dict()V1写法，改为model_dump
            **log_data.model_dump()
        )
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
        call_sign: Optional[str] = None
    ) -> tuple[List[QSOLog], int]:
        """获取日志列表"""
        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False
        )
        
        # 应用过滤条件
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
        
        # 排序
        query = query.order_by(QSOLog.qso_date.desc())
        
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        return logs, total
    
    @staticmethod
    def get_log(db: Session, log_id: int, user_id: int) -> QSOLog:
        """获取单条日志"""
        log = db.query(QSOLog).filter(
            QSOLog.id == log_id,
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False
        ).first()
        
        if not log:
            raise ValueError("Log not found")
        
        return log
    
    @staticmethod
    def update_log(db: Session, log_id: int, user_id: int, log_data: QSOLogUpdate) -> QSOLog:
        """更新日志"""
        db_log = LogService.get_log(db, log_id, user_id)
        
        # 更新字段
        update_data = log_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_log, key, value)
        
        db.commit()
        db.refresh(db_log)
        return db_log
    
    @staticmethod
    def delete_log(db: Session, log_id: int, user_id: int):
        """删除日志（逻辑删除）"""
        db_log = LogService.get_log(db, log_id, user_id)
        db_log.is_deleted = True
        db.commit()
    
    @staticmethod
    def get_stats(db: Session, user_id: int) -> dict:
        """获取日志统计"""
        from sqlalchemy import func
        
        query = db.query(QSOLog).filter(
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False
        )
        
        total_qso = query.count()
        
        # DXCC统计
        total_dxcc = db.query(
            func.count(func.distinct(QSOLog.call_sign))
        ).filter(
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False
        ).scalar()
        
        # QSL统计
        qsl_sent = query.filter(QSOLog.qsl_sent == "Y").count()
        qsl_rcvd = query.filter(QSOLog.qsl_rcvd == "Y").count()
        eqsl_sent = query.filter(QSOLog.eqsl_sent == "Y").count()
        eqsl_rcvd = query.filter(QSOLog.eqsl_rcvd == "Y").count()
        lotw_confirmed = query.filter(QSOLog.lotw_rcvd == "Y").count()
        
        # 距离统计
        distance_sum = db.query(
            func.sum(QSOLog.distance)
        ).filter(
            QSOLog.user_id == user_id,
            QSOLog.is_deleted == False,
            QSOLog.distance.isnot(None)
        ).scalar() or 0
        
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
