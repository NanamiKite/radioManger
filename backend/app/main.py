from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.api.v1 import (
    auth_router,
    users_router,
    logs_router,
    stations_router,
    locations_router,
    stats_router,
    callsigns_router,
    sync_router,
    shortcuts_router,
    dxcluster_router,
    map_router,
    udp_router,
)
from app.api.v1.admin import router as admin_router
from app.database.base import engine, Base
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.dxcluster_manager import dxcluster_manager

import app.models

# 自动创建数据库表（首次启动时）
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期钩子：startup 时不做主动连接（等用户触发），
    shutdown 时确保 DX Cluster telnet 连接被干净关闭。"""
    yield
    await dxcluster_manager.disconnect()


app = FastAPI(
    title="RadioManager API",
    description="Amateur Radio Log Management System API",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "Accept"])
# 中间件顺序：后添加的先执行请求。执行顺序：RateLimit → Logging → ErrorHandler → CORS
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

# 路由 - 共12个模块
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(logs_router, prefix=f"{settings.API_V1_STR}/logs", tags=["logs"])
app.include_router(stations_router, prefix=f"{settings.API_V1_STR}/stations", tags=["stations"])
app.include_router(locations_router, prefix=f"{settings.API_V1_STR}/locations", tags=["locations"])
app.include_router(stats_router, prefix=f"{settings.API_V1_STR}/stats", tags=["stats"])
app.include_router(callsigns_router, prefix=f"{settings.API_V1_STR}/callsigns", tags=["callsigns"])
app.include_router(sync_router, prefix=f"{settings.API_V1_STR}/sync", tags=["sync"])
app.include_router(shortcuts_router, prefix=f"{settings.API_V1_STR}/shortcuts", tags=["shortcuts"])
app.include_router(dxcluster_router, prefix=f"{settings.API_V1_STR}/dxcluster", tags=["dxcluster"])
app.include_router(map_router, prefix=f"{settings.API_V1_STR}/map", tags=["map"])
app.include_router(udp_router, prefix=f"{settings.API_V1_STR}/udp", tags=["udp"])

# Admin 路由 - 仅服务器模式（MySQL）启用
if settings.DATABASE_MODE != "sqlite":
    app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])

@app.get("/health")
async def health_check():
    result = {
        "status": "ok",
        "version": settings.VERSION,
        "database": settings.DATABASE_MODE,
        "subsystems": {},
    }

    # 数据库连接检查
    try:
        from app.database.session import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            result["subsystems"]["database"] = "ok"
        finally:
            db.close()
    except Exception:
        result["subsystems"]["database"] = "error"
        result["status"] = "degraded"

    # Redis 连接检查（MySQL 模式）
    if settings.DATABASE_MODE == "mysql":
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
            r.ping()
            result["subsystems"]["redis"] = "ok"
        except Exception:
            result["subsystems"]["redis"] = "error"
            result["status"] = "degraded"

    # SQLite 路径信息（前端设置页需要）
    if settings.DATABASE_MODE == "sqlite":
        import os
        db_path = os.path.abspath(settings.SQLITE_PATH)
        result["db_path"] = db_path
        result["db_dir"] = os.path.dirname(db_path)

    return result

@app.get("/")
async def root():
    return {"name": "RadioManager API", "version": settings.VERSION, "docs": "/docs", "database_mode": settings.DATABASE_MODE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=settings.WORKERS)
