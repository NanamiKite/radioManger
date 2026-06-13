"""
Middleware - 日志记录中间件
"""

import logging
from fastapi import Request
from time import time

logger = logging.getLogger("radiomanager.middleware")

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        start_time = time()
        
        response = await call_next(request)
        
        process_time = time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
