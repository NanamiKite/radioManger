"""管理员认证依赖注入"""
from fastapi import Depends
from app.models.user import User
from app.dependencies import get_current_user
from app.exceptions import PermissionException
from app.config import settings


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """检查当前用户是否为管理员（仅服务器模式生效）"""
    if settings.DATABASE_MODE == "sqlite":
        # 本地模式不做权限检查
        return current_user
    if current_user.role != "admin":
        raise PermissionException("Admin access required")
    if not current_user.is_active:
        raise PermissionException("Account disabled")
    return current_user
