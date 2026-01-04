"""
FastAPI Server - Production Ready
Removes mock data, implements real integrations
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
from redis import asyncio as aioredis

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# Import orchestrator with proper error handling
try:
    from rainmaker_orchestrator import Orchestrator
    orchestrator_available = True
    logger.info("Orchestrator module loaded successfully")
except ImportError as e:
    orchestrator_available = False
    logger.error(f"Failed to import orchestrator: {e}")
    logger.warning("Server will start but orchestrator endpoints will return 503")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Starting Lab-Verse API Server")

    # Initialize Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.state.redis = await aioredis.from_url(redis_url, decode_responses=True)
    logger.info(f"Connected to Redis at {redis_url}")

    # Initialize HTTP client for external APIs
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("HTTP client initialized")

    # Initialize orchestrator if available
    if orchestrator_available:
        app.state.orchestrator = Orchestrator()
        logger.info("Orchestrator initialized")

    yield

    # Shutdown
    logger.info("Shutting down Lab-Verse API Server")
    await app.state.redis.close()
    await app.state.http_client.aclose()
    logger.info("Connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="Lab-Verse Monitoring API",
    description="Production-ready API for Lab-Verse monitoring system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]


class MarketIntelRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    refresh_cache: bool = Field(default=False)


class MarketIntelResponse(BaseModel):
    company: str
    data: Optional[Dict[str, Any]]
    source: str
    cached: bool
    timestamp: str


class OrchestratorRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = Field(default=None)
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)


# Dependency to check orchestrator availability
async def require_orchestrator():
    """Ensure orchestrator is available"""
    if not orchestrator_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator service is not available. Check server logs."
        )


# Dependency to get Redis
async def get_redis():
    """Get Redis connection"""
    return app.state.redis


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(redis = Depends(get_redis)):
    """Health check endpoint for monitoring"""
    services = {}

    # Check Redis
    try:
        await redis.ping()
        services["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = "unhealthy"

    # Check Orchestrator
    services["orchestrator"] = "healthy" if orchestrator_available else "unavailable"

    # Overall status
    all_healthy = all(v == "healthy" for v in services.values() if v != "unavailable")

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        services=services
    )


# Market Intelligence Endpoint - REAL IMPLEMENTATION
@app.post("/api/market-intel", response_model=MarketIntelResponse)
async def get_market_intel(
    request: MarketIntelRequest,
    redis = Depends(get_redis)
):
    """
    Get market intelligence for a company
    Uses real API integration with caching
    """
    cache_key = f"market_intel:{request.company_name.lower()}"

    # Check cache first (unless refresh requested)
    if not request.refresh_cache:
        cached_data = await redis.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {request.company_name}")
            import json
            return MarketIntelResponse(
                company=request.company_name,
                data=json.loads(cached_data),
                source="cache",
                cached=True,
                timestamp=datetime.utcnow().isoformat()
            )

    # Fetch from real API (example: using a search API)
    try:
        search_api_key = os.getenv("SEARCH_API_KEY")
        if not search_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search API not configured. Set SEARCH_API_KEY environment variable."
            )

        # Example: Using Perplexity API or similar
        async with app.state.http_client as client:
            response = await client.post(
                os.getenv("SEARCH_API_URL", "https://api.perplexity.ai/chat/completions"),
                headers={
                    "Authorization": f"Bearer {search_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-small-online",
                    "messages": [{
                        "role": "user",
                        "content": f"Provide current market intelligence for {request.company_name}: recent news, stock performance, key metrics, competitive position."
                    }]
                }
            )

            if response.status_code != 200:
                logger.error(f"Search API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to fetch market intelligence from external API"
                )

            api_data = response.json()
            intelligence = {
                "summary": api_data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "fetched_at": datetime.utcnow().isoformat()
            }

            # Cache for 1 hour
            import json
            await redis.setex(cache_key, 3600, json.dumps(intelligence))

            return MarketIntelResponse(
                company=request.company_name,
                data=intelligence,
                source="live_api",
                cached=False,
                timestamp=datetime.utcnow().isoformat()
            )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching market intel: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External API request failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching market intel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching market intelligence"
        )


# Orchestrator proxy endpoint
@app.post("/api/orchestrate")
async def orchestrate_request(
    request: OrchestratorRequest,
    _ = Depends(require_orchestrator)
):
    """
    Route requests through the Python orchestrator
    """
    try:
        result = await app.state.orchestrator.process_request(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}"
        )


# HubSpot webhook endpoint
@app.post("/webhook/hubspot")
async def hubspot_webhook(
    payload: Dict[str, Any],
    _ = Depends(require_orchestrator)
):
    """
    Handle HubSpot webhook events
    """
    try:
        event_type = payload.get("subscriptionType")
        logger.info(f"Received HubSpot webhook: {event_type}")

        # Process through orchestrator
        result = await app.state.orchestrator.handle_hubspot_event(payload)

        return JSONResponse(content={
            "status": "processed",
            "event_type": event_type,
            "result": result
        })
    except Exception as e:
        logger.error(f"HubSpot webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )