from pydantic_settings import BaseSettings
from typing import List
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
    DATABASE_URL: str = "mysql+pymysql://radiomanager:password123@localhost:3306/radiomanager"
    SQLALCHEMY_ECHO: bool = False
    
    # JWT设置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS设置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:7777",
    ]
    
    # Redis设置
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
    ENABLE_TEST_ACCOUNT: bool = False  # 开发模式下启用测试账号
    TEST_ACCOUNT_USERNAME: str = "testuser"
    TEST_ACCOUNT_PASSWORD: str = "test123456"
    TEST_ACCOUNT_EMAIL: str = "test@radiomanager.local"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
