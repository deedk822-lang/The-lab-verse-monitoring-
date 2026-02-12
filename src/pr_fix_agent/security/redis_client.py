from __future__ import annotations

import asyncio

import redis.asyncio as aioredis
from redis.asyncio import Redis

from pr_fix_agent.core.config import Settings, get_settings

# Module-level client and lock for thread-safe initialization
class RedisContainer:
    client: Redis | None = None
    init_lock: asyncio.Lock | None = None

_container = RedisContainer()


def _get_lock() -> asyncio.Lock:
    """Get or create the initialization lock."""
    if _container.init_lock is None:
        _container.init_lock = asyncio.Lock()
    return _container.init_lock


async def get_redis_client(settings: Settings | None = None) -> Redis:
    """
    Get Redis client for rate limiting (thread-safe).

    ✅ FIX #1: Remove incorrect await on aioredis.from_url (it's synchronous)
    ✅ FIX #2: Add asyncio.Lock to prevent race conditions

    Uses double-check locking pattern:
    1. Check if client exists (fast path, no lock)
    2. Acquire lock
    3. Re-check if client exists (another coroutine may have created it)
    4. Create client if needed
    5. Release lock
    """

    # Fast path: client already exists
    if _container.client is not None:
        return _container.client

    # Slow path: need to create client (thread-safe)
    lock = _get_lock()
    async with lock:
        # Double-check: another coroutine may have created it while we waited
        if _container.client is not None:
            return _container.client

        # Create client
        if settings is None:
            settings = get_settings()

        # ✅ FIX: aioredis.from_url is synchronous - don't await it
        _container.client = aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )

        return _container.client


async def close_redis() -> None:
    """Close Redis connection (thread-safe)."""

    if _container.client is not None:
        lock = _get_lock()
        async with lock:
            if _container.client is not None:
                await _container.client.close()
                _container.client = None
