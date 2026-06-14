from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""

    # 应用基本设置
    APP_NAME: str = "RadioManager"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    WORKERS: int = 4
    ENVIRONMENT: str = "production"  # development, staging, production

    # 数据库设置
    # DATABASE_MODE: sqlite | mysql | postgresql
    DATABASE_MODE: str = "sqlite"
    # SQLite本地数据库路径 (仅 DATABASE_MODE=sqlite 时生效)
    # 使用绝对路径避免工作目录问题
    SQLITE_URL: str = "sqlite:///./radiomanager.db"
    SQLITE_PATH: str = "./radiomanager.db"
    # MySQL连接字符串 (仅 DATABASE_MODE=mysql 时生效)
    DATABASE_URL: str = "mysql+pymysql://radiomanager:password123@localhost:3306/radiomanager"
    SQLALCHEMY_ECHO: bool = False

    @property
    def ACTIVE_DATABASE_URL(self) -> str:
        """根据模式返回活跃的数据库连接串"""
        if self.DATABASE_MODE == "sqlite":
            return self.SQLITE_URL
        return self.DATABASE_URL

    # JWT设置
    SECRET_KEY: str = "radioManager-development-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS设置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:7777",
    ]

    # Redis设置 (仅局域网/云部署使用)
    REDIS_URL: str = "redis://localhost:6379"

    # QRZ API设置
    QRZ_USERNAME: str = ""
    QRZ_PASSWORD: str = ""
    QRZ_API_URL: str = "https://xmldata.qrz.com/xml/current/"

    # GitHub设置
    GITHUB_TOKEN: str = ""

    # 邮件设置
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@radiomanager.local"

    # 日志设置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # 文件上传设置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = ["adi", "adif"]

    # 开发模式设置
    ENABLE_TEST_ACCOUNT: bool = True   # 本地开发默认启用测试账号
    TEST_ACCOUNT_USERNAME: str = "admin"
    TEST_ACCOUNT_PASSWORD: str = "admin123"
    TEST_ACCOUNT_EMAIL: str = "admin@radiomanager.dev"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
