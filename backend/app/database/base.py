from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# 构建engine参数
engine_kwargs = {
    "echo": settings.SQLALCHEMY_ECHO,
}

if settings.DATABASE_MODE == "sqlite":
    # SQLite无需连接池
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # MySQL/PostgreSQL使用连接池
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

# 创建数据库引擎
engine = create_engine(
    settings.ACTIVE_DATABASE_URL,
    **engine_kwargs,
)

# SQLite：启用WAL模式提升并发性能
if settings.DATABASE_MODE == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建声明式基类
Base = declarative_base()
