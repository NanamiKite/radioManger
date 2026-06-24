"""缓存服务 - SQLite模式使用内存缓存，MySQL模式使用Redis"""

import logging
import json
from typing import Optional, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("radiomanager.cache")


class MemoryCache:
    """内存缓存（SQLite 本地模式使用）"""

    def __init__(self):
        self._cache: dict = {}
        self._ttl: dict = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        if key in self._ttl:
            if datetime.now(timezone.utc).replace(tzinfo=None) > self._ttl[key]:
                self.delete(key)
                return None
        return self._cache[key]

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self._cache[key] = value
        if ttl_seconds > 0:
            self._ttl[key] = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=ttl_seconds)

    def delete(self, key: str):
        self._cache.pop(key, None)
        self._ttl.pop(key, None)

    def clear(self):
        self._cache.clear()
        self._ttl.clear()

    def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False
        if key in self._ttl and datetime.now(timezone.utc).replace(tzinfo=None) > self._ttl[key]:
            self.delete(key)
            return False
        return True


class RedisCache:
    """Redis 缓存（服务器部署模式使用）"""

    def __init__(self, redis_client):
        self._redis = redis_client

    def get(self, key: str) -> Optional[Any]:
        try:
            data = self._redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis GET error for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        try:
            serialized = json.dumps(value)
            if ttl_seconds > 0:
                self._redis.setex(key, ttl_seconds, serialized)
            else:
                self._redis.set(key, serialized)
        except Exception as e:
            logger.warning(f"Redis SET error for key '{key}': {e}")

    def delete(self, key: str):
        try:
            self._redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis DELETE error for key '{key}': {e}")

    def clear(self):
        try:
            self._redis.flushdb()
        except Exception as e:
            logger.warning(f"Redis FLUSHDB error: {e}")

    def exists(self, key: str) -> bool:
        try:
            return bool(self._redis.exists(key))
        except Exception as e:
            logger.warning(f"Redis EXISTS error for key '{key}': {e}")
            return False


def _create_cache():
    """根据 DATABASE_MODE 创建对应的缓存实例"""
    from app.config import settings

    if settings.DATABASE_MODE == "mysql":
        try:
            import redis
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            logger.info("Redis connected, using RedisCache")
            return RedisCache(client)
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to MemoryCache")
            return MemoryCache()
    return MemoryCache()


# 全局缓存实例
cache = _create_cache()
