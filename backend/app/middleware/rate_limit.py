"""速率限制中间件"""

import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("radiomanager.middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简易内存速率限制中间件"""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 跳过静态资源和健康检查
        if request.url.path in ("/health", "/") or request.url.path.startswith("/docs"):
            return await call_next(request)

        # 获取客户端标识
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # 清理过期记录
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        # 检查限制
        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "Too many requests. Please try again later.",
                    "data": None,
                },
            )

        # 记录请求
        self._requests[client_ip].append(now)
        return await call_next(request)
