import redis.asyncio as aioredis

from src.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def get_redis() -> aioredis.Redis:
    """Get the Redis client instance."""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
