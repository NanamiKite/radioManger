"""
RadioManager Release Server
首次启动自动初始化数据库+管理员，挂载前端 SPA
"""

import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from pathlib import Path
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings

# 用不同变量名避免与 app 包冲突
from app.main import app as application
from app.database.base import engine, SessionLocal, Base

# ── 首次启动：建表 + 创建管理员 ──
import app.models  # noqa
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    from app.models.user import User
    from app.utils.security import SecurityUtils
    admin = db.query(User).filter(User.username == settings.TEST_ACCOUNT_USERNAME).first()
    if not admin:
        admin = User(
            username=settings.TEST_ACCOUNT_USERNAME,
            email=settings.TEST_ACCOUNT_EMAIL,
            password_hash=SecurityUtils.hash_password(settings.TEST_ACCOUNT_PASSWORD),
            full_name="Administrator",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"  ✓ Admin created: {settings.TEST_ACCOUNT_USERNAME} / {settings.TEST_ACCOUNT_PASSWORD}")
    else:
        print(f"  ✓ Admin exists: {admin.username}")
finally:
    db.close()

# ── 前端 SPA 挂载 ──
frontend_dist = Path(__file__).parent / "frontend_dist"

if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        application.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    class SPAFallbackMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            path = request.url.path
            if path.startswith("/api") or path.startswith("/docs") \
               or path.startswith("/redoc") or path.startswith("/openapi") \
               or path.startswith("/assets") or path == "/health":
                return await call_next(request)
            file_path = frontend_dist / path.lstrip("/")
            if file_path.is_file():
                return FileResponse(str(file_path))
            if request.method == "GET":
                index = frontend_dist / "index.html"
                if index.exists():
                    return FileResponse(str(index))
            return await call_next(request)

    application.add_middleware(SPAFallbackMiddleware)

if __name__ == "__main__":
    print("=" * 50)
    print("  RadioManager v2.4.1")
    print("  http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(application, host="0.0.0.0", port=8000)
