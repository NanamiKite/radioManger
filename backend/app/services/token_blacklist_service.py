"""Token 黑名单服务 - logout 时使 token 失效

SQLite 模式：内存 set 存储（进程重启后失效，可接受）
MySQL 模式：Redis 存储，持久化且带 TTL 自动过期
"""

import logging
from typing import Set
from app.config import settings

logger = logging.getLogger("radiomanager.token_blacklist")


class MemoryBlacklist:
    """内存黑名单（SQLite 本地模式）"""

    def __init__(self):
        self._tokens: Set[str] = set()

    def add(self, jti: str, ttl_seconds: int = 0):
        self._tokens.add(jti)

    def is_blacklisted(self, jti: str) -> bool:
        return jti in self._tokens

    def remove(self, jti: str):
        self._tokens.discard(jti)


class RedisBlacklist:
    """Redis 黑名单（服务器部署模式）"""

    def __init__(self, redis_client):
        self._redis = redis_client

    def add(self, jti: str, ttl_seconds: int = 0):
        key = f"blacklist:{jti}"
        try:
            if ttl_seconds > 0:
                self._redis.setex(key, ttl_seconds, "1")
            else:
                self._redis.set(key, "1")
            logger.info(f"Token {jti[:8]}... added to blacklist (ttl={ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Redis blacklist ADD error: {e}")

    def is_blacklisted(self, jti: str) -> bool:
        key = f"blacklist:{jti}"
        try:
            return bool(self._redis.exists(key))
        except Exception as e:
            logger.error(f"Redis blacklist CHECK error: {e}")
            return False

    def remove(self, jti: str):
        key = f"blacklist:{jti}"
        try:
            self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis blacklist REMOVE error: {e}")


def _create_blacklist():
    """根据 DATABASE_MODE 创建对应的黑名单实例"""
    if settings.DATABASE_MODE == "mysql":
        try:
            import redis
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            logger.info("Redis connected, using RedisBlacklist for token management")
            return RedisBlacklist(client)
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to MemoryBlacklist")
            return MemoryBlacklist()
    return MemoryBlacklist()


# 全局黑名单实例
token_blacklist = _create_blacklist()
