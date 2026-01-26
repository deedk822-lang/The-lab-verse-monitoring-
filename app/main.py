"""
Enhanced main application with security, monitoring, and distributed state.
"""

import os
import time
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from collections import OrderedDict

from fastapi import FastAPI, Request, Response, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
import redis.asyncio as redis

from vaal_ai_empire.api.sanitizers import sanitize_webhook_payload
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_async_session
from vaal_ai_empire.api.shared_state import RedisDedupeCache, RedisRateLimiter
from agent.tools.llm_provider import initialize_from_env, get_global_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fallback in-memory state for non-distributed environments
class InMemoryDedupeCache:
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict[str, float] = OrderedDict()

    def _cleanup(self):
        current_time = time.time()
        expired = [k for k, ts in self._cache.items() if current_time - ts > self.ttl_seconds]
        for k in expired: del self._cache[k]

    def generate_key(self, payload: Dict[str, Any]) -> str:
        webhook_id = payload.get('webhookEvent', payload.get('id', ''))
        timestamp = payload.get('timestamp', payload.get('created_at', ''))
        unique_str = f"{webhook_id}:{timestamp}:{str(payload)[:100]}"
        return hashlib.sha256(unique_str.encode()).hexdigest()

    async def is_duplicate(self, key: str) -> bool:
        self._cleanup()
        if key in self._cache: return True
        self._cache[key] = time.time()
        if len(self._cache) > self.max_size: self._cache.popitem(last=False)
        return False

class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = {}

    async def is_allowed(self, key: str) -> bool:
        now = time.time()
        if key not in self._requests: self._requests[key] = []
        cutoff = now - self.window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
        if len(self._requests[key]) >= self.max_requests: return False
        self._requests[key].append(now)
        return True

# Global state components (initialized in lifespan)
dedupe_cache: Union[RedisDedupeCache, InMemoryDedupeCache] = InMemoryDedupeCache()
rate_limiter: Union[RedisRateLimiter, InMemoryRateLimiter] = InMemoryRateLimiter()
redis_client: Optional[redis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global dedupe_cache, rate_limiter, redis_client

    logger.info("Starting VAAL AI Empire application")

    # Initialize Redis if available
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await redis_client.ping()

            dedupe_cache = RedisDedupeCache(
                redis_client,
                ttl_seconds=int(os.getenv('WEBHOOK_DEDUPE_TTL', '300'))
            )
            rate_limiter = RedisRateLimiter(
                redis_client,
                max_requests=int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '60')),
                window_seconds=60
            )
            logger.info("Distributed state initialized via Redis")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}. Falling back to in-memory state.")
    else:
        logger.info("REDIS_URL not set. Using in-memory state (not suitable for multiple replicas).")

    # Initialize LLM provider
    try:
        initialize_from_env()
    except Exception as e:
        logger.error(f"Failed to initialize LLM provider: {e}")

    yield

    # Shutdown
    if redis_client:
        await redis_client.close()
    logger.info("Shutting down VAAL AI Empire application")


# Initialize FastAPI app
app = FastAPI(
    title="VAAL AI Empire",
    description="Multi-provider LLM system with security hardening",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configuration
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true',
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security dependencies
async def verify_self_healing_key(
    x_self_healing_key: Optional[str] = Header(None)
) -> bool:
    """Verify self-healing webhook authentication key."""
    expected_key = os.getenv('SELF_HEALING_KEY')
    if not expected_key:
        logger.warning("SELF_HEALING_KEY not configured - webhook auth disabled")
        return True

    if not x_self_healing_key or x_self_healing_key != expected_key:
        logger.warning("Invalid or missing self-healing key")
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True

async def check_rate_limit(request: Request) -> bool:
    """Check rate limit for client."""
    if os.getenv('RATE_LIMIT_ENABLED', 'true').lower() != 'true':
        return True

    client_ip = request.client.host
    if not await rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return True

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

@app.get("/ready")
async def readiness_check():
    checks = {"llm_provider": False, "redis": False}
    try:
        get_global_provider()
        checks["llm_provider"] = True
    except: pass

    if redis_client:
        try:
            await redis_client.ping()
            checks["redis"] = True
        except: pass

    all_ready = checks["llm_provider"]
    status_code = 200 if all_ready else 503
    return JSONResponse(status_code=status_code, content={"ready": all_ready, "checks": checks})

@app.get("/metrics")
async def metrics():
    from app.metrics import metrics_endpoint
    return metrics_endpoint()

@app.post("/webhooks/atlassian")
async def atlassian_webhook(
    request: Request,
    authenticated: bool = Depends(verify_self_healing_key),
    rate_limited: bool = Depends(check_rate_limit)
):
    try:
        raw_payload = await request.json()
        dedupe_key = dedupe_cache.generate_key(raw_payload)
        if await dedupe_cache.is_duplicate(dedupe_key):
            logger.info(f"Duplicate webhook received: {dedupe_key[:16]}")
            return {"status": "duplicate", "message": "Event already processed"}

        payload = sanitize_webhook_payload(raw_payload)
        standard_payload = convert_atlassian_payload(payload)
        result = await forward_webhook(standard_payload)

        return {"status": "success", "message": "Webhook processed", "result": result}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def convert_atlassian_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    event_type = payload.get('webhookEvent', 'unknown')
    standard = {
        "event_type": event_type,
        "timestamp": payload.get('timestamp', datetime.now(timezone.utc).isoformat()),
        "source": "atlassian",
        "data": {}
    }
    if 'issue' in payload:
        standard['data']['issue'] = {
            "key": payload['issue'].get('key'),
            "summary": payload['issue'].get('fields', {}).get('summary'),
            "status": payload['issue'].get('fields', {}).get('status', {}).get('name'),
            "assignee": payload['issue'].get('fields', {}).get('assignee', {}).get('displayName'),
            "description": payload['issue'].get('description', payload['issue'].get('fields', {}).get('description'))
        }
    if 'comment' in payload:
        standard['data']['comment'] = {
            "body": payload['comment'].get('body'),
            "author": payload['comment'].get('author', {}).get('displayName')
        }
    if 'pullRequest' in payload:
        standard['data']['pull_request'] = {
            "id": payload['pullRequest'].get('id'),
            "title": payload['pullRequest'].get('title'),
            "state": payload['pullRequest'].get('state'),
            "author": payload['pullRequest'].get('author', {}).get('displayName')
        }
    return standard

async def forward_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    event_type = payload.get('event_type', '')
    if 'jira' in event_type.lower() or 'issue' in payload.get('data', {}):
        target_url = os.getenv('JIRA_BASE_URL')
        auth = (os.getenv('JIRA_USER_EMAIL'), os.getenv('JIRA_API_TOKEN'))
    elif 'bitbucket' in event_type.lower() or 'pull_request' in payload.get('data', {}):
        target_url = os.getenv('BITBUCKET_BASE_URL')
        auth = (os.getenv('BITBUCKET_USERNAME'), os.getenv('BITBUCKET_APP_PASSWORD'))
    else:
        return {"status": "skipped", "reason": "unknown_type"}

    if not target_url: return {"status": "error", "reason": "missing_config"}

    try:
        async with create_ssrf_safe_async_session(timeout=float(os.getenv('WEBHOOK_TIMEOUT', '30'))) as client:
            response = await client.post(target_url, json=payload, auth=auth)
            response.raise_for_status()
            return {"status": "forwarded", "status_code": response.status_code, "target": target_url}
    except Exception as e:
        logger.error(f"Error forwarding webhook: {e}")
        return {"status": "error", "error": str(e)}

@app.post("/api/generate")
async def generate_text(request: Request, rate_limited: bool = Depends(check_rate_limit)):
    from agent.tools.llm_provider import TaskType
    try:
        data = await request.json()
        prompt = data.get('prompt', '')
        task = TaskType[data.get('task', 'TEXT_GENERATION')]
        provider = get_global_provider()
        response = await provider.generate_with_retry(
            prompt=prompt, task=task,
            max_tokens=data.get('max_tokens', 1000),
            temperature=data.get('temperature', 0.7)
        )
        return {
            "text": response.text, "model": response.model,
            "provider": response.provider, "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms
        }
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv('PORT', '8000')))
