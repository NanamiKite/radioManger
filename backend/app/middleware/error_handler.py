"""全局错误处理中间件"""

import logging
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
