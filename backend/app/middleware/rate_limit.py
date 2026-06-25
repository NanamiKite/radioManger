"""速率限制中间件"""

import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("radiomanager.middleware")

# 可信代理 IP 白名单（在此列表中的代理 IP 才会读取 X-Forwarded-For）
TRUSTED_PROXIES = {"127.0.0.1", "::1"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简易内存速率限制中间件"""

    # 敏感端点独立限流（更严格）
    STRICT_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/change-password",
        "/api/v1/auth/confirm-delete",
    }
    STRICT_MAX = 5  # 5次/分钟

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP（支持反向代理）"""
        client_ip = request.client.host if request.client else "unknown"
        # 仅可信代理才读取 X-Forwarded-For
        if client_ip in TRUSTED_PROXIES:
            forwarded = request.headers.get("x-forwarded-for", "")
            if forwarded:
                # 取第一个 IP（最左边的是原始客户端）
                return forwarded.split(",")[0].strip()
        return client_ip

    async def dispatch(self, request: Request, call_next):
        # 跳过静态资源和健康检查
        if request.url.path in ("/health", "/") or request.url.path.startswith("/docs"):
            return await call_next(request)

        # 获取客户端标识
        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        # 用路径区分限流桶
        is_strict = request.url.path in self.STRICT_PATHS
        bucket = f"{client_ip}:strict" if is_strict else client_ip
        limit = self.STRICT_MAX if is_strict else self.max_requests

        # 清理过期记录
        self._requests[bucket] = [
            t for t in self._requests[bucket] if t > window_start
        ]
        if not self._requests[bucket]:
            del self._requests[bucket]

        # 检查限制
        if len(self._requests.get(bucket, [])) >= limit:
            logger.warning(f"Rate limit exceeded for {bucket}")
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "Too many requests. Please try again later.",
                    "data": None,
                },
            )

        # 记录请求
        self._requests[bucket].append(now)
        return await call_next(request)
