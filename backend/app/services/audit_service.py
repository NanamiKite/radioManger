"""审计日志服务"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """审计日志服务 - 记录用户操作"""

    @staticmethod
    def log(
        db: Session,
        user: User,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """记录审计日志"""
        entry = AuditLog(
            user_id=user.id,
            username=user.username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()

    @staticmethod
    def get_logs(
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """获取审计日志列表"""
        query = db.query(AuditLog)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        total = query.count()
        items = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
