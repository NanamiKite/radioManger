from datetime import datetime, timezone, timedelta
import math
from typing import Optional
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from app.config import settings

# 密码加密
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

class TokenExpiredError(Exception):
    """Token 已过期"""
    pass

class InvalidTokenError(Exception):
    """Token 无效"""
    pass


def validate_password(password: str) -> str:
    """Enforce the same limits before validation and bcrypt hashing."""
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return password


class SecurityUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        validate_password(password)
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        if len(plain_password.encode("utf-8")) > 72:
            return False
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, str]:
        """创建JWT令牌，返回 (token, jti)"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        jti = str(uuid4())
        to_encode.update({"exp": expire, "jti": jti, "token_type": "access"})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt, jti

    @staticmethod
    def decode_token(token: str) -> dict:
        """解码JWT令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"require": ["exp", "sub", "jti", "token_type"]},
            )
            if (
                payload.get("token_type") != "access"
                or not isinstance(payload.get("sub"), str)
                or not payload["sub"].isascii()
                or len(payload["sub"]) > 19
                or not payload["sub"].isdigit()
                or int(payload["sub"]) <= 0
                or int(payload["sub"]) > 9223372036854775807
                or not isinstance(payload.get("jti"), str)
                or not payload["jti"]
                or len(payload["jti"]) > 100
                or isinstance(payload.get("exp"), bool)
                or not isinstance(payload.get("exp"), (int, float))
                or not math.isfinite(payload["exp"])
            ):
                raise InvalidTokenError("Invalid access token claims")
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token expired")
        except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError):
            raise InvalidTokenError("Invalid token")
