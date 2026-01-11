import redis
import os

# Default to localhost for Docker/Dev, allow override for Vercel/Prod
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_conn = redis.from_url(REDIS_URL, decode_responses=True)
    # Quick connectivity check
    redis_conn.ping()
    print(f"✅ Connected to Redis at {REDIS_URL}")
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    redis_conn = None
