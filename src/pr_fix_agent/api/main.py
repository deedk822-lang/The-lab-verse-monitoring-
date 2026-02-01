"""
FastAPI application for PR Fix Agent
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from ..core.config import settings
from ..observability.metrics import REQUEST_COUNT, REQUEST_LATENCY, lifespan_metrics
from ..security.validator import RateLimiter, SecurityValidator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager"""
    # Startup
    async with lifespan_metrics():
        yield
    # Shutdown


def create_app() -> FastAPI:
    """Create FastAPI application"""

    app = FastAPI(
        title="PR Fix Agent API",
        description="Enterprise-grade AI-powered PR error fixing system",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Security middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure for production

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware
    rate_limiter = RateLimiter()

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Simple IP-based rate limiting
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        if not await rate_limiter.is_allowed(key):
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
            )

        response = await call_next(request)
        return response

    # Metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = REQUEST_LATENCY.time()

        response = await call_next(request)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(REQUEST_LATENCY.time() - start_time)

        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        import structlog
        logger = structlog.get_logger("api.error")
        logger.error("Unhandled exception", exc_info=exc)

        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": "0.1.0"}

    # Metrics endpoint
    if settings.observability.enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # API v1 routes
    from .v1 import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")

    return app