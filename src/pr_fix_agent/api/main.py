"""
Main FastAPI Application for PR Fix Agent.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
import structlog

from pr_fix_agent.core.config import get_settings
from pr_fix_agent.observability.logging import configure_logging
from pr_fix_agent.observability.metrics import initialize_metrics, http_requests_total, http_request_duration_seconds
from pr_fix_agent.observability.tracing import initialize_tracing
from pr_fix_agent.security.middleware import SecurityHeadersMiddleware, RequestIDMiddleware, AuditLoggingMiddleware
from pr_fix_agent.security.redis_client import close_redis
from pr_fix_agent.db.session import close_db

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings)
    initialize_metrics()
    initialize_tracing(settings)
    logger.info("application_started", version=settings.version, environment=settings.environment)
    yield
    await close_redis()
    await close_db()
    logger.info("application_stopped")


app = FastAPI(
    title="PR Fix Agent API",
    description="Enterprise-grade AI-powered PR error fixing",
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path
    with http_request_duration_seconds.labels(method=method, path=path).time():
        response = await call_next(request)
    http_requests_total.labels(method=method, path=path, status_code=response.status_code).inc()
    return response


@app.get("/healthz", tags=["Health"])
async def health_check():
    return {"status":"healthy","version":settings.version}


@app.get("/metrics", tags=["Observability"])
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
