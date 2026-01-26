"""
Enhanced main application with security, monitoring, and webhook handling.
"""

import os
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import OrderedDict

from fastapi import FastAPI, Request, Response, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx

from vaal_ai_empire.api.sanitizers import (
    sanitize_webhook_payload,
    RateLimiter
)
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_async_session
from agent.tools.llm_provider import LLMProviderFactory, set_global_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Webhook deduplication cache
class DedupeCache:
    """Thread-safe TTL cache for webhook deduplication."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict[str, float] = OrderedDict()

    def _cleanup(self):
        """Remove expired entries."""
        current_time = time.time()
        expired = [
            key for key, timestamp in self._cache.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        for key in expired:
            del self._cache[key]

    def is_duplicate(self, key: str) -> bool:
        """Check if key exists and add it."""
        self._cleanup()

        if key in self._cache:
            return True

        # Add to cache
        self._cache[key] = time.time()

        # Enforce max size
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

        return False

    def generate_key(self, payload: Dict[str, Any]) -> str:
        """Generate unique key for payload."""
        # Use webhook ID and timestamp if available
        webhook_id = payload.get('webhookEvent', payload.get('id', ''))
        timestamp = payload.get('timestamp', payload.get('created_at', ''))

        unique_str = f"{webhook_id}:{timestamp}:{str(payload)[:100]}"
        return hashlib.sha256(unique_str.encode()).hexdigest()


# Initialize global components
dedupe_cache = DedupeCache(
    ttl_seconds=int(os.getenv('WEBHOOK_DEDUPE_TTL', '300')),
    max_size=int(os.getenv('WEBHOOK_DEDUPE_MAX_SIZE', '1000'))
)

rate_limiter = RateLimiter(
    max_requests=int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '60')),
    window_seconds=60
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting VAAL AI Empire application")

    # Initialize LLM provider
    provider_type = os.getenv('LLM_PROVIDER', 'huggingface')
    logger.info(f"Initializing LLM provider: {provider_type}")

    from agent.tools.llm_provider import LLMConfig

    config_map = {
        'huggingface': LLMConfig(
            api_key=os.getenv('HF_TOKEN')
        ),
        'zai': LLMConfig(
            api_key=os.getenv('ZAI_API_KEY'),
            base_url=os.getenv('ZAI_BASE_URL'),
            timeout=float(os.getenv('ZAI_TIMEOUT', '60'))
        ),
        'qwen': LLMConfig(
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_BASE_URL'),
            timeout=float(os.getenv('QWEN_TIMEOUT', '60'))
        ),
        'openai': LLMConfig(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL'),
            timeout=float(os.getenv('OPENAI_TIMEOUT', '60'))
        )
    }

    config = config_map.get(provider_type)
    if config:
        kwargs = {}
        if provider_type == 'huggingface':
            try:
                from agent.tools.hf_model_loader import model_loader
                kwargs['model_loader'] = model_loader
            except ImportError:
                logger.warning("hf_model_loader not found, HuggingFaceProvider will be limited")

        provider = LLMProviderFactory.create(provider_type, config, **kwargs)
        set_global_provider(provider)
        logger.info(f"LLM provider {provider_type} initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down VAAL AI Empire application")


# Initialize FastAPI app
app = FastAPI(
    title="VAAL AI Empire",
    description="Multi-provider LLM system with security hardening",
    version="2.0.0",
    lifespan=lifespan
)

# Add middleware
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
    if not os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true':
        return True

    client_ip = request.client.host
    current_time = time.time()

    if not rate_limiter.is_allowed(client_ip, current_time):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return True


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Check critical dependencies
    checks = {
        "llm_provider": False,
        "database": False,
    }

    try:
        from agent.tools.llm_provider import get_global_provider
        get_global_provider()
        checks["llm_provider"] = True
    except Exception as e:
        logger.error(f"LLM provider check failed: {e}")

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from app.metrics import metrics_endpoint
    return metrics_endpoint()


# Webhook endpoints
@app.post("/webhooks/atlassian")
async def atlassian_webhook(
    request: Request,
    authenticated: bool = Depends(verify_self_healing_key),
    rate_limited: bool = Depends(check_rate_limit)
):
    """
    Handle Atlassian webhooks with security and deduplication.
    """
    try:
        # Parse payload
        raw_payload = await request.json()

        # Check for duplicates
        dedupe_key = dedupe_cache.generate_key(raw_payload)
        if dedupe_cache.is_duplicate(dedupe_key):
            logger.info(f"Duplicate webhook received: {dedupe_key[:16]}")
            return {"status": "duplicate", "message": "Event already processed"}

        # Sanitize payload
        payload = sanitize_webhook_payload(raw_payload)

        # Convert to standard format
        standard_payload = convert_atlassian_payload(payload)

        # Forward to appropriate endpoint
        result = await forward_webhook(standard_payload)

        return {
            "status": "success",
            "message": "Webhook processed",
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def convert_atlassian_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Atlassian webhook to standard format."""
    event_type = payload.get('webhookEvent', 'unknown')

    standard = {
        "event_type": event_type,
        "timestamp": payload.get('timestamp', datetime.utcnow().isoformat()),
        "source": "atlassian",
        "data": {}
    }

    # Extract relevant data based on event type
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
    """Forward webhook to appropriate service with error handling."""
    source = payload.get('source')
    event_type = payload.get('event_type')

    # Determine target endpoint
    if 'jira' in event_type.lower() or 'issue' in payload.get('data', {}):
        target_url = os.getenv('JIRA_BASE_URL')
        auth = (
            os.getenv('JIRA_USER_EMAIL'),
            os.getenv('JIRA_API_TOKEN')
        )
    elif 'bitbucket' in event_type.lower() or 'pull_request' in payload.get('data', {}):
        target_url = os.getenv('BITBUCKET_BASE_URL')
        auth = (
            os.getenv('BITBUCKET_USERNAME'),
            os.getenv('BITBUCKET_APP_PASSWORD')
        )
    else:
        logger.warning(f"Unknown webhook type: {event_type}")
        return {"status": "skipped", "reason": "unknown_type"}

    if not target_url:
        logger.error(f"Target URL not configured for {event_type}")
        return {"status": "error", "reason": "missing_config"}

    # Forward request with SSRF protection
    try:
        async with create_ssrf_safe_async_session(
            timeout=float(os.getenv('WEBHOOK_TIMEOUT', '30'))
        ) as client:
            response = await client.post(
                target_url,
                json=payload,
                auth=auth
            )
            response.raise_for_status()

            return {
                "status": "forwarded",
                "status_code": response.status_code,
                "target": target_url
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error forwarding webhook: {e.response.status_code}")
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}",
            "details": e.response.text[:200]
        }
    except httpx.RequestError as e:
        logger.error(f"Request error forwarding webhook: {e}")
        return {
            "status": "error",
            "error": "request_failed",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error forwarding webhook: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "unexpected",
            "details": str(e)
        }


# API endpoints
@app.post("/api/generate")
async def generate_text(
    request: Request,
    rate_limited: bool = Depends(check_rate_limit)
):
    """Generate text using LLM provider."""
    from agent.tools.llm_provider import get_global_provider, TaskType

    try:
        data = await request.json()
        prompt = data.get('prompt', '')
        task = TaskType[data.get('task', 'TEXT_GENERATION')]

        provider = get_global_provider()
        response = await provider.generate_with_retry(
            prompt=prompt,
            task=task,
            max_tokens=data.get('max_tokens', 1000),
            temperature=data.get('temperature', 0.7)
        )

        return {
            "text": response.text,
            "model": response.model,
            "provider": response.provider,
            "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms
        }

    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', '8000')),
        reload=os.getenv('DEBUG', 'false').lower() == 'true',
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )
