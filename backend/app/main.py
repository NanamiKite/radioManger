from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, users, logs, stations, stats
from app.database.base import engine  # ✔ 正确位置
from app.database.base import Base

import app.models 

Base.metadata.create_all(bind=engine)


# 创建FastAPI应用
app = FastAPI(
    title="RadioManager API",
    description="Amateur Radio Log Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(logs.router, prefix=f"{settings.API_V1_STR}/logs", tags=["logs"])
app.include_router(stations.router, prefix=f"{settings.API_V1_STR}/stations", tags=["stations"])
app.include_router(stats.router, prefix=f"{settings.API_V1_STR}/stats", tags=["stats"])

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 根路由
@app.get("/")
async def root():
    return {
        "name": "RadioManager API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=settings.WORKERS
    )
from fastapi import Request
import time

# @app.middleware("http") 调试日志打印
# async def log_requests(request: Request, call_next):
#     body = await request.body()
#     print("\n===== REQUEST =====")
#     print("URL:", request.url)
#     print("METHOD:", request.method)
#     print("BODY:", body.decode())

#     response = await call_next(request)

#     print("STATUS:", response.status_code)
#     print("===================\n")
#     return response