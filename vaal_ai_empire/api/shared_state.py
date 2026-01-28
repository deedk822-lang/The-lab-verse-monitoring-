"""
Shared state management using Redis.
"""

import hashlib
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisDedupeCache:
    """Redis-backed deduplication cache."""

    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 300):
        self.redis = redis_client
        self.ttl = ttl_seconds

    def generate_key(self, payload: Dict[str, Any]) -> str:
        """Generate unique key for payload."""
        dump = json.dumps(payload, sort_keys=True)
        return "dedupe:" + hashlib.sha256(dump.encode()).hexdigest()

    async def is_duplicate(self, key: str) -> bool:
        """Check if key exists, if not set it."""
        is_new = await self.redis.set(key, "1", ex=self.ttl, nx=True)
        return not is_new

class RedisRateLimiter:
    """Redis-backed rate limiter (sliding window)."""

    def __init__(self, redis_client: redis.Redis, max_requests: int = 60, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for key."""
        rk = f"ratelimit:{key}"
        async with self.redis.pipeline(transaction=True) as pipe:
            now = time.time()
            member = f"{now}-{uuid.uuid4()}"
            pipe.zremrangebyscore(rk, 0, now - self.window)
            pipe.zcard(rk) # Get count before adding new
            pipe.zadd(rk, {member: now})
            pipe.expire(rk, self.window)
            _, count, _, _ = await pipe.execute()

        return count < self.max_requests
