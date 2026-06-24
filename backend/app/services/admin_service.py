"""管理员服务 - 用户管理"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.qso_log import QSOLog
from app.models.station import Station
from app.utils.security import SecurityUtils


class AdminService:
    """管理员服务"""

    @staticmethod
    def get_users(
        db: Session,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple:
        """获取用户列表"""
        query = db.query(User).filter(User.is_deleted == False)
        if keyword:
            query = query.filter(
                (User.username.ilike(f"%{keyword}%")) |
                (User.email.ilike(f"%{keyword}%"))
            )
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        total = query.count()
        items = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_user_detail(db: Session, user_id: int) -> Optional[User]:
        """获取用户详情"""
        return db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

    @staticmethod
    def toggle_user(db: Session, user_id: int) -> Optional[User]:
        """启用/禁用用户"""
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if user:
            user.is_active = not user.is_active
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> Optional[User]:
        """重置用户密码"""
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if user:
            user.password_hash = SecurityUtils.hash_password(new_password)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """软删除用户"""
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if user:
            user.is_deleted = True
            user.is_active = False
            db.commit()
            return True
        return False

    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> dict:
        """获取用户统计摘要（不含QSO内容）"""
        qso_count = db.query(func.count(QSOLog.id)).filter(
            QSOLog.user_id == user_id, QSOLog.is_deleted == False
        ).scalar() or 0

        station_count = db.query(func.count(Station.id)).filter(
            Station.user_id == user_id, Station.is_deleted == False
        ).scalar() or 0

        return {
            "qso_count": qso_count,
            "station_count": station_count,
        }
