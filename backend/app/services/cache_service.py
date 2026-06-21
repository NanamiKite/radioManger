"""缓存服务"""

import logging
from typing import Optional, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("radiomanager.cache")


class CacheService:
    """应用缓存服务（内存缓存，可选Redis扩展）"""

    def __init__(self):
        self._cache: dict = {}
        self._ttl: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None

        # 检查TTL
        if key in self._ttl:
            if datetime.now(timezone.utc).replace(tzinfo=None) > self._ttl[key]:
                self.delete(key)
                return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """设置缓存（默认5分钟TTL）"""
        self._cache[key] = value
        if ttl_seconds > 0:
            self._ttl[key] = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=ttl_seconds)

    def delete(self, key: str):
        """删除缓存"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)

    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._ttl.clear()

    def exists(self, key: str) -> bool:
        """判断缓存是否存在且未过期"""
        if key not in self._cache:
            return False
        if key in self._ttl and datetime.now(timezone.utc).replace(tzinfo=None) > self._ttl[key]:
            self.delete(key)
            return False
        return True


# 全局缓存实例
cache = CacheService()
