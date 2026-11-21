from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.exceptions import RadioManagerException
from app.services.session_service import SessionService
from app.models.user import User
from app.schemas.user import UserRegister, UserUpdate
from app.utils.security import SecurityUtils

class UserService:
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        """获取用户（通过用户名）"""
        return db.query(User).filter(User.username == username, User.is_deleted == False).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """获取用户（通过邮箱）"""
        return db.query(User).filter(User.email == email, User.is_deleted == False).first()
    
    @staticmethod
    def create_user(db: Session, user_data: UserRegister) -> User:
        """创建用户"""
        # 检查密码匹配
        if user_data.password != user_data.confirm_password:
            raise ValueError("Passwords do not match")
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise RadioManagerException("Username already exists", 409)
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise RadioManagerException("Email already registered", 409)
        
        # 创建用户
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=SecurityUtils.hash_password(user_data.password),
            full_name=user_data.full_name,
            timezone=user_data.timezone,
            language=user_data.language
        )
        
        db.add(db_user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # Resolve only actual unique-name/email conflicts; other constraints propagate.
            if db.query(User).filter(User.username == user_data.username).first():
                raise RadioManagerException("Username already exists", 409)
            if db.query(User).filter(User.email == user_data.email).first():
                raise RadioManagerException("Email already registered", 409)
            raise
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """认证用户。失败返回 None（不区分原因，防止用户枚举）"""
        user = UserService.get_user_by_username(db, username)

        if not user or not SecurityUtils.verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        return user
    
    @staticmethod
    def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
        """更新用户信息"""
        update_data = user_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> User:
        """修改密码"""
        if not SecurityUtils.verify_password(old_password, user.password_hash):
            raise ValueError("Old password is incorrect")
        
        user.password_hash = SecurityUtils.hash_password(new_password)
        SessionService.remove_all_sessions(db, user.id)
        db.commit()
        db.refresh(user)
        return user
