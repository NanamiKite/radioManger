"""
错误处理模块
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

class RadioManagerException(Exception):
    """应用基础异常"""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code

class AuthException(RadioManagerException):
    """认证异常"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)

class ValidationException(RadioManagerException):
    """验证异常"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

class NotFoundException(RadioManagerException):
    """资源不存在异常"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)

class PermissionException(RadioManagerException):
    """权限异常"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)

async def exception_handler(request: Request, exc: RadioManagerException):
    """全局异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "data": None
        }
    )
