"""
خدمة الـ caching مع Redis. تُعطَّل بأمان عند غياب الاتصال.
"""
import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger("ataeru.cache")

class CacheService:
    """خدمة الـ caching مع Redis (redis.asyncio)."""

    def __init__(self, redis_url: str = None):
        self.redis = None
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(
                redis_url or settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # تحقق من الاتصال حتى نُعطّل الخدمة بأمان عند غياب Redis
            import asyncio
            asyncio.run(client.ping())
            self.redis = client
            logger.info("Redis cache service initialized")
        except Exception as e:
            logger.warning(f"Redis unavailable, cache disabled: {e}")
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        """جلب من الـ cache."""
        if not self.redis:
            return None
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Cache hit: {key}")
                return json.loads(data)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None):
        """حفظ في الـ cache."""
        if not self.redis:
            return
        try:
            await self.redis.setex(
                key,
                ttl if ttl is not None else settings.CACHE_TTL,
                json.dumps(value, default=str),
            )
            logger.debug(f"Cache set: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str):
        """حذف من الـ cache."""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    async def clear_pattern(self, pattern: str):
        """حذف جميع المفاتيح المطابقة."""
        if not self.redis:
            return
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.debug(f"Cache cleared {len(keys)} keys matching {pattern}")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    # --- دوال متزامنة لاستخدامها داخل handlers متزامنة (threadpool) ---

    def get_sync(self, key: str) -> Optional[Any]:
        import asyncio
        try:
            return asyncio.run(self.get(key))
        except RuntimeError:
            return None

    def set_sync(self, key: str, value: Any, ttl: int = None):
        import asyncio
        try:
            asyncio.run(self.set(key, value, ttl))
        except RuntimeError:
            pass

    def delete_sync(self, key: str):
        import asyncio
        try:
            asyncio.run(self.delete(key))
        except RuntimeError:
            pass

cache_service = CacheService()
