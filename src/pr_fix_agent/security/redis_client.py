"""
S3: Redis Client for Distributed Rate Limiting
"""

from __future__ import annotations

import redis.asyncio as aioredis
from redis.asyncio import Redis

from pr_fix_agent.core.config import Settings, get_settings

_redis_client: Redis | None = None


async def get_redis_client(settings: Settings | None = None) -> Redis:
    """Get Redis client."""
    global _redis_client

    if _redis_client is None:
        if settings is None:
            settings = get_settings()

        _redis_client = await aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
