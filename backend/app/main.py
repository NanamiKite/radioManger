from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
)
from app.database.base import engine, Base
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware

import app.models

# 自动创建数据库表（首次启动时）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RadioManager API",
    description="Amateur Radio Log Management System API",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# 路由 - 共9个模块
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(logs_router, prefix=f"{settings.API_V1_STR}/logs", tags=["logs"])
app.include_router(stations_router, prefix=f"{settings.API_V1_STR}/stations", tags=["stations"])
app.include_router(locations_router, prefix=f"{settings.API_V1_STR}/locations", tags=["locations"])
app.include_router(stats_router, prefix=f"{settings.API_V1_STR}/stats", tags=["stats"])
app.include_router(callsigns_router, prefix=f"{settings.API_V1_STR}/callsigns", tags=["callsigns"])
app.include_router(sync_router, prefix=f"{settings.API_V1_STR}/sync", tags=["sync"])
app.include_router(shortcuts_router, prefix=f"{settings.API_V1_STR}/shortcuts", tags=["shortcuts"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": settings.DATABASE_MODE}

@app.get("/")
async def root():
    return {"name": "RadioManager API", "version": "2.1.0", "docs": "/docs", "database_mode": settings.DATABASE_MODE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=settings.WORKERS)
