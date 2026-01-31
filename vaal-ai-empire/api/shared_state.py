"""
Shared state management using Redis for distributed rate limiting and deduplication.
"""

import hashlib
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

class RedisDedupeCache:
    """Redis-backed TTL cache for webhook deduplication."""

    def __init__(self, redis_client, ttl_seconds: int = 300):
        self.redis = redis_client
        self.ttl = ttl_seconds

    def generate_key(self, payload: Dict[str, Any]) -> str:
        """Generate unique key for payload."""
        webhook_id = payload.get('webhookEvent', payload.get('id', ''))
        timestamp = payload.get('timestamp', payload.get('created_at', ''))
        unique_str = f"{webhook_id}:{timestamp}:{str(payload)[:100]}"
        return hashlib.sha256(unique_str.encode()).hexdigest()

    async def is_duplicate(self, key: str) -> bool:
        """Check if key exists in Redis, if not add it."""
        try:
            # SET NX returns True if set, None/False if already exists
            result = await self.redis.set(
                f"dedupe:{key}",
                str(time.time()),
                ex=self.ttl,
                nx=True
            )
            return result is None or result is False
        except Exception as e:
            logger.error(f"Redis dedupe check failed: {e}")
            return False  # Fallback: allow request on Redis failure

class RedisRateLimiter:
    """Redis-backed distributed rate limiter using sliding window."""

    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        redis_key = f"rate_limit:{key}"

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                # Real redis-py pipeline methods are not async
                pipe.zremrangebyscore(redis_key, 0, now - self.window)
                pipe.zcard(redis_key)
                pipe.zadd(redis_key, {str(now): now})
                pipe.expire(redis_key, self.window)

                results = await pipe.execute()

            if results and len(results) > 1:
                current_count = results[1]
                # Handle cases where current_count might be a Mock in tests
                if hasattr(current_count, '__lt__'):
                    return current_count < self.max_requests

            return True
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return True  # Fallback: allow request on Redis failure
