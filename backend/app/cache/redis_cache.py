"""
Redis & In-Memory Fallback Cache Layer
Provides low-latency key-value caching with TTL and automatic fallback.
"""
import json
import time
from typing import Any, Optional
from app.config.settings import settings
from app.monitoring.logger import logger
from app.monitoring.metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class InMemoryCache:
    """Fast in-memory key-value cache with timestamp expiry."""

    def __init__(self, max_items: int = 10000):
        self._store: dict[str, tuple[str, float]] = {}
        self._max_items = max_items

    def get(self, key: str) -> Optional[str]:
        if key in self._store:
            val, exp = self._store[key]
            if exp == 0 or exp > time.time():
                return val
            else:
                del self._store[key]
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None):
        if len(self._store) >= self._max_items:
            # Evict 20% oldest items
            now = time.time()
            expired = [k for k, (_, exp) in self._store.items() if exp != 0 and exp <= now]
            for k in expired:
                del self._store[k]
            if len(self._store) >= self._max_items:
                keys_to_remove = list(self._store.keys())[: self._max_items // 5]
                for k in keys_to_remove:
                    del self._store[k]

        exp = (time.time() + ex) if ex else 0
        self._store[key] = (value, exp)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


class CacheService:
    """Unified cache service managing Redis connection and fallback."""

    def __init__(self):
        self.redis_client = None
        self.fallback = InMemoryCache()
        self.is_connected = False

    async def connect(self):
        """Initializes Redis connection if configured."""
        if not settings.CACHE_ENABLED or not settings.REDIS_URL or not HAS_REDIS:
            self.is_connected = False
            return

        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0,
            )
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Connected to Redis cache successfully.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis ({e}). Using in-memory fallback cache.")
            self.is_connected = False
            self.redis_client = None

    async def close(self):
        """Closes Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False

    async def get_json(self, key: str, cache_type: str = "general") -> Optional[Any]:
        """Retrieves and deserializes JSON from cache."""
        try:
            val_str = None
            if self.is_connected and self.redis_client:
                val_str = await self.redis_client.get(key)
            else:
                val_str = self.fallback.get(key)

            if val_str:
                CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()
                return json.loads(val_str)
            else:
                CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()
                return None
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None

    async def set_json(self, key: str, data: Any, ttl: Optional[int] = None):
        """Serializes and saves data to cache."""
        try:
            val_str = json.dumps(data, ensure_ascii=False)
            if self.is_connected and self.redis_client:
                await self.redis_client.set(key, val_str, ex=ttl)
            else:
                self.fallback.set(key, val_str, ex=ttl)
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")

    async def delete(self, key: str):
        """Deletes a key from cache."""
        try:
            if self.is_connected and self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.fallback.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")


cache_service = CacheService()
