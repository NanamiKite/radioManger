"""
初始化数据库模型
"""

from app.database.base import engine, Base
from app.models import user, station, qso_log, callsign_cache, statistics

def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

if __name__ == "__main__":
    init_db()
