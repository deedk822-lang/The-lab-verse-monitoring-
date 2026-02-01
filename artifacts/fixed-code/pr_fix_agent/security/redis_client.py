"""
Thread-Safe Redis Client - Global Production Standard (S3)
FIXED: Race condition in client creation, proper async/sync usage
"""

import asyncio
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from pr_fix_agent.core.config import Settings

_redis_client: Optional[Redis] = None
_redis_init_lock = asyncio.Lock()

async def get_redis_client(settings: Optional[Settings] = None) -> Redis:
    """
    Get or create thread-safe Redis client.

    ✅ FIX: Uses asyncio.Lock to prevent race conditions
    ✅ FIX: Double-check pattern for performance
    ✅ FIX: Proper initialization of aioredis
    """
    global _redis_client

    # Fast path: client already exists
    if _redis_client is not None:
        return _redis_client

    # Slow path: create client with lock protection
    async with _redis_init_lock:
        # Double-check inside lock
        if _redis_client is not None:
            return _redis_client

        if settings is None:
            from pr_fix_agent.core.config import get_settings
            settings = get_settings()

        # ✅ FIX: aioredis.from_url is synchronous in creation, but returns async client
        # We use the async-compatible client from redis-py 4.x+
        _redis_client = aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )

        return _redis_client


async def close_redis():
    """Close Redis client connection."""
    global _redis_client
    async with _redis_init_lock:
        if _redis_client is not None:
            await _redis_client.close()
            _redis_client = None
