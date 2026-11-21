import secrets
import warnings
from functools import lru_cache
from typing import List, Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用配置"""

    # 应用基本设置
    APP_NAME: str = "RadioManager"
    VERSION: str = "2.6.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    WORKERS: int = Field(default=1, ge=1, le=1)
    ENVIRONMENT: Literal["development", "staging", "production"] = "production"

    # 数据库设置
    # DATABASE_MODE: sqlite | mysql
    DATABASE_MODE: Literal["sqlite", "mysql"] = "sqlite"
    # SQLite本地数据库路径 (仅 DATABASE_MODE=sqlite 时生效)
    # 使用绝对路径避免工作目录问题
    SQLITE_URL: str = "sqlite:///./radiomanager.db"
    SQLITE_PATH: str = "./radiomanager.db"
    # MySQL连接字符串 (仅 DATABASE_MODE=mysql 时生效，必须在 .env 中设置)
    DATABASE_URL: str = ""
    SQLALCHEMY_ECHO: bool = False

    @property
    def ACTIVE_DATABASE_URL(self) -> str:
        """根据模式返回活跃的数据库连接串"""
        if self.DATABASE_MODE == "sqlite":
            return self.SQLITE_URL
        return self.DATABASE_URL

    # JWT设置
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60

    # CORS设置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:7777",
    ]


    # QRZ API设置
    QRZ_USERNAME: str = ""
    QRZ_PASSWORD: str = ""
    QRZ_API_URL: str = "https://xmldata.qrz.com/xml/current/"

    # GitHub设置
    GITHUB_TOKEN: str = ""

    # UDP 监听设置
    UDP_WSJTX_PORT: int = Field(default=2237, ge=1024, le=65535)
    UDP_N1MM_PORT: int = Field(default=12060, ge=1024, le=65535)
    UDP_ENABLED: bool = False
    UDP_BIND_HOST: str = "127.0.0.1"
    UDP_ALLOWED_SOURCES: List[str] = ["127.0.0.1", "::1"]
    DX_CLUSTER_NODES: List[str] = []

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
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = ["adi", "adif"]

    # 服务器模式管理员设置
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""
    ADMIN_EMAIL: str = "admin@radiomanager.local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",
    )

    @model_validator(mode="after")
    def validate_deployment(self):
        if self.DATABASE_MODE == "mysql" and not self.DATABASE_URL:
            raise ValueError("DATABASE_MODE=mysql requires DATABASE_URL")
        for node in self.DX_CLUSTER_NODES:
            try:
                endpoint = urlsplit("//" + node)
                port = endpoint.port
                if (not endpoint.hostname or port is None or not 1 <= port <= 65535
                        or endpoint.username is not None or endpoint.password is not None
                        or endpoint.path or endpoint.query or endpoint.fragment
                        or any(character.isspace() for character in node)):
                    raise ValueError("invalid endpoint")
            except ValueError as exc:
                raise ValueError("DX_CLUSTER_NODES entries must be host:port (IPv6 must use [address]:port)") from exc
        if self.ENVIRONMENT == "production":
            key = self.SECRET_KEY.lower()
            if len(self.SECRET_KEY) < 32 or any(
                marker in key for marker in ("placeholder", "change", "your-secret", "your_secret", "your-super-secret", "default", "radiomanager-local-test")
            ):
                raise ValueError("Production SECRET_KEY must be a random secret of at least 32 characters")
        elif not self.SECRET_KEY:
            warnings.warn("Missing SECRET_KEY: using an ephemeral development key", stacklevel=2)
            self.SECRET_KEY = secrets.token_hex(32)
        if self.ADMIN_PASSWORD and (len(self.ADMIN_PASSWORD) < 8 or len(self.ADMIN_PASSWORD.encode("utf-8")) > 72):
            raise ValueError("ADMIN_PASSWORD must contain at least 8 characters and at most 72 UTF-8 bytes")
        return self

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
