"""全局错误处理中间件"""

import logging
import sqlite3
from sqlalchemy.exc import DBAPIError, OperationalError, TimeoutError as DatabaseTimeoutError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.exceptions import RadioManagerException

logger = logging.getLogger("radiomanager.middleware")


def _database_unavailable(exc: Exception) -> bool:
    if isinstance(exc, DatabaseTimeoutError):
        return True
    if not isinstance(exc, DBAPIError):
        return False
    if exc.connection_invalidated:
        return True
    if not isinstance(exc, OperationalError):
        return False

    sqlite_code = getattr(exc.orig, "sqlite_errorcode", None)
    if sqlite_code is not None:
        # Mask extended codes; missing tables and malformed SQL are not outages.
        return sqlite_code & 0xFF in (
            sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED,
            sqlite3.SQLITE_CANTOPEN, sqlite3.SQLITE_IOERR,
        )

    driver_code = exc.orig.args[0] if exc.orig.args else None
    # MySQL connection limits, resolution/connect failures, shutdown and disconnects.
    return driver_code in (1040, 1042, 1053, 1203, 2002, 2003, 2005, 2006, 2013, 2055)


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
            unavailable = _database_unavailable(exc)
            status_code = 503 if unavailable else 500
            logger.exception("Database unavailable" if unavailable else "Unhandled error")
            return JSONResponse(
                status_code=status_code,
                content={
                    "code": status_code,
                    "message": "Database unavailable" if unavailable else "Internal server error",
                    "data": None,
                },
            )
