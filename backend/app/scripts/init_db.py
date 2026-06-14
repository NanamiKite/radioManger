"""
数据库初始化脚本
用法: python -m app.scripts.init_db

初始化所有数据库表并创建默认管理员账户。
支持 SQLite（本地开发）和 MySQL（生产部署）。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.database.base import Base, engine
from app.config import settings
from app.models import (  # noqa: F401 - register all models
    User, Station, QSOLog, CallsignCache, Statistics,
    LogFile, SyncHistory, DeletedLog,
)


def init_database():
    """初始化数据库"""
    print(f"🔧 RadioManager Database Initialization")
    print(f"   Mode: {settings.DATABASE_MODE}")
    print(f"   URL: {settings.ACTIVE_DATABASE_URL}")

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created.")

    # 在开发模式下自动创建测试账户
    if settings.ENABLE_TEST_ACCOUNT:
        from app.scripts.create_admin import create_admin
        create_admin(
            username=settings.TEST_ACCOUNT_USERNAME,
            password=settings.TEST_ACCOUNT_PASSWORD,
            email=settings.TEST_ACCOUNT_EMAIL,
        )

    print("✅ Database initialization complete.")
    print(f"   Tables: {list(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    # 切换到 backend 目录确保 SQLite 路径正确
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(backend_dir)
    init_database()
