import json
import hashlib
from typing import Optional
import redis.asyncio as aioredis
from .config import get_settings

settings = get_settings()


class RedisCache:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        try:
            self.redis = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis.ping()
        except Exception:
            self.redis = None

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    def _make_key(self, prefix: str, data: str) -> str:
        digest = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{digest}"

    async def get(self, prefix: str, key_data: str) -> Optional[str]:
        if not self.redis:
            return None
        return await self.redis.get(self._make_key(prefix, key_data))

    async def set(self, prefix: str, key_data: str, value: str, ttl: int = None):
        if not self.redis:
            return
        ttl = ttl or settings.cache_ttl
        await self.redis.setex(self._make_key(prefix, key_data), ttl, value)

    async def get_json(self, prefix: str, key_data: str) -> Optional[dict]:
        val = await self.get(prefix, key_data)
        if val:
            return json.loads(val)
        return None

    async def set_json(self, prefix: str, key_data: str, value: dict, ttl: int = None):
        await self.set(prefix, key_data, json.dumps(value, ensure_ascii=False), ttl)


cache = RedisCache()
