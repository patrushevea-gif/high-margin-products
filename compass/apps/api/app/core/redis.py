import redis.asyncio as aioredis
from arq.connections import ArqRedis, create_pool, RedisSettings
from app.core.config import get_settings

_redis: aioredis.Redis | None = None
_arq_pool: ArqRedis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_arq_pool() -> ArqRedis:
    """Arq pool for enqueueing background tasks from the API layer."""
    global _arq_pool
    if _arq_pool is None:
        settings = get_settings()
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _arq_pool


async def close_redis() -> None:
    global _redis, _arq_pool
    if _redis:
        await _redis.aclose()
        _redis = None
    if _arq_pool:
        await _arq_pool.aclose()
        _arq_pool = None
