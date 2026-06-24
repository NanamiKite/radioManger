"""
数据库初始化脚本
用法: python -m app.scripts.init_db

初始化所有数据库表并创建默认管理员账户。
支持 SQLite（本地开发）和 MySQL（生产部署）。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.database.base import Base, engine, SessionLocal
from app.config import settings
from app.models import (  # noqa: F401 - register all models
    User, Station, QSOLog, CallsignCache, Statistics,
    LogFile, SyncHistory, DeletedLog,
    AuditLog, UserSession, SystemConfig,
)


def _migrate_columns():
    """轻量列迁移：给已有表补充缺失的列（不删除、不修改已有列）"""
    from sqlalchemy import text as sql_text
    db = SessionLocal()
    try:
        with db.bind.connect() as conn:
            # ── users 表新增列 ──
            if settings.DATABASE_MODE == "mysql":
                rows = conn.execute(sql_text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'"
                )).fetchall()
                existing = {row[0] for row in rows}
            else:
                rows = conn.execute(sql_text("PRAGMA table_info(users)")).fetchall()
                existing = {row[1] for row in rows}

            migrations = {
                "deletion_scheduled_at": {
                    "sqlite": "ALTER TABLE users ADD COLUMN deletion_scheduled_at DATETIME",
                    "mysql":  "ALTER TABLE users ADD COLUMN deletion_scheduled_at DATETIME NULL",
                },
                "deletion_cancelled": {
                    "sqlite": "ALTER TABLE users ADD COLUMN deletion_cancelled BOOLEAN DEFAULT 0",
                    "mysql":  "ALTER TABLE users ADD COLUMN deletion_cancelled BOOLEAN DEFAULT FALSE",
                },
            }
            mode = settings.DATABASE_MODE
            for col, ddls in migrations.items():
                if col not in existing:
                    conn.execute(sql_text(ddls.get(mode, ddls["sqlite"])))
                    print(f"  ✅ Added column users.{col}")

            conn.commit()
    except Exception as e:
        # 表可能还不存在（全新安装），create_all 会处理
        print(f"  ℹ️  Column migration skipped: {e}")
    finally:
        db.close()


def init_database():
    """初始化数据库"""
    print(f"🔧 RadioManager Database Initialization")
    print(f"   Mode: {settings.DATABASE_MODE}")
    print(f"   URL: {settings.ACTIVE_DATABASE_URL}")

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created.")

    # 补充已有表的缺失列（create_all 不会 ALTER 已有表）
    _migrate_columns()

    if settings.DATABASE_MODE == "mysql":
        # 服务器模式：从配置创建管理员
        admin_user = settings.ADMIN_USERNAME
        admin_pass = settings.ADMIN_PASSWORD
        admin_email = settings.ADMIN_EMAIL
        if admin_user and admin_pass:
            from app.scripts.create_admin import create_admin
            create_admin(
                username=admin_user,
                password=admin_pass,
                email=admin_email,
            )
        else:
            print("⚠️  ADMIN_USERNAME / ADMIN_PASSWORD not set, skipping admin creation.")
    else:
        # 本地模式：创建测试账户
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
