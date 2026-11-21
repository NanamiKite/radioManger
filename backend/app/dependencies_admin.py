"""管理员认证依赖注入"""
from fastapi import Depends
from app.models.user import User
from app.dependencies import get_current_user
from app.exceptions import PermissionException
from app.config import settings


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require administrator privileges in every database mode."""
    if current_user.role != "admin":
        raise PermissionException("Admin access required")
    if not current_user.is_active:
        raise PermissionException("Account disabled")
    return current_user


def get_realtime_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Local realtime controls require login; server controls require an admin."""
    if settings.DATABASE_MODE == "mysql":
        return get_current_admin(current_user)
    return current_user
