from __future__ import annotations

import asyncio
from functools import lru_cache

import redis.asyncio as aioredis
from redis.asyncio import Redis

from pr_fix_agent.core.config import Settings, get_settings

# Module-level client and lock for thread-safe initialization
_redis_client: Redis | None = None
_redis_init_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    """Get or create the initialization lock."""
    global _redis_init_lock
    if _redis_init_lock is None:
        _redis_init_lock = asyncio.Lock()
    return _redis_init_lock


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
    global _redis_client

    # Fast path: client already exists
    if _redis_client is not None:
        return _redis_client

    # Slow path: need to create client (thread-safe)
    lock = _get_lock()
    async with lock:
        # Double-check: another coroutine may have created it while we waited
        if _redis_client is not None:
            return _redis_client

        # Create client
        if settings is None:
            settings = get_settings()

        # ✅ FIX: aioredis.from_url is synchronous - don't await it
        _redis_client = aioredis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )

        return _redis_client


async def close_redis() -> None:
    """Close Redis connection (thread-safe)."""
    global _redis_client

    if _redis_client is not None:
        lock = _get_lock()
        async with lock:
            if _redis_client is not None:
                await _redis_client.close()
                _redis_client = None
