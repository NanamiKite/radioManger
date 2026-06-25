"""全局错误处理中间件"""

import logging
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.exceptions import RadioManagerException

logger = logging.getLogger("radiomanager.middleware")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """统一错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RadioManagerException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": exc.status_code,
                    "message": exc.message,
                    "data": None,
                },
            )
        except HTTPException as exc:
            # 保留 FastAPI 原始状态码（401/403/404 等），不吞成 500
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": exc.status_code,
                    "message": exc.detail or "Error",
                    "data": None,
                },
            )
        except Exception as exc:
            logger.exception(f"Unhandled error: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "Internal server error",
                    "data": None,
                },
            )
