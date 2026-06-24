"""
数据库初始化脚本
用法: python -m app.scripts.init_db

初始化所有数据库表并创建默认管理员账户。
支持 SQLite（本地开发）和 MySQL（生产部署）。
使用 Alembic 管理数据库迁移。
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


def _has_tables():
    """检查数据库中是否已有表"""
    from sqlalchemy import inspect
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return len(tables) > 0
    except Exception:
        return False


def _get_alembic_config():
    """获取 Alembic 配置"""
    from alembic.config import Config
    # alembic.ini 在 backend/ 目录下
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    alembic_cfg = Config(ini_path, attributes={"configure_loggers": False})
    # 设置绝对路径
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.ACTIVE_DATABASE_URL)
    return alembic_cfg


def _run_alembic_upgrade():
    """运行 Alembic 迁移"""
    from alembic import command
    alembic_cfg = _get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    print("  ✅ Alembic migrations applied")


def _stamp_alembic():
    """标记当前数据库版本为最新（用于全新安装）"""
    from alembic import command
    alembic_cfg = _get_alembic_config()
    command.stamp(alembic_cfg, "head")
    print("  ✅ Alembic stamped at head")


def init_database():
    """初始化数据库"""
    print(f"🔧 RadioManager Database Initialization")
    print(f"   Mode: {settings.DATABASE_MODE}")
    print(f"   URL: {settings.ACTIVE_DATABASE_URL}")

    if _has_tables():
        # 已有表：尝试运行 Alembic 迁移
        print("   Existing database detected, running migrations...")
        try:
            _run_alembic_upgrade()
        except Exception as e:
            print(f"  ⚠️  Alembic migration failed: {e}")
            print("     This is expected if tables were created before Alembic was configured.")
            print("     Stamping current version...")
            try:
                _stamp_alembic()
            except Exception:
                pass
    else:
        # 全新数据库：create_all + stamp
        print("   Fresh database, creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("  ✅ All database tables created.")
        try:
            _stamp_alembic()
        except Exception as e:
            print(f"  ⚠️  Alembic stamp failed: {e}")

    # 创建管理员
    if settings.DATABASE_MODE == "mysql":
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
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(backend_dir)
    init_database()
