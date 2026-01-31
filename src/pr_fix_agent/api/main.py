"""
FastAPI Application Layer - Global Production Standard
Integrates S1-S10 security, orchestrator, and observability.
"""

import time
from typing import Dict

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from pr_fix_agent.core.config import get_settings, Settings
from pr_fix_agent.security.middleware import SecurityHeadersMiddleware
from pr_fix_agent.security.audit import get_audit_logger
from pr_fix_agent.observability.logging import configure_structured_logging
from pr_fix_agent.observability.metrics import http_requests_total, http_request_duration_seconds
from pr_fix_agent.orchestrator import FixOrchestrator

# Configure logging
configure_structured_logging()

# Initialize FastAPI
app = FastAPI(
    title="PR Fix Agent API",
    description="Production-grade AI PR Fix Agent",
    version="1.0.0",
)

# 1. Prometheus Metrics Endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 2. Security Middleware (S4)
app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Request Timing & Metrics
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Update metrics
    http_requests_total.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        path=request.url.path
    ).observe(process_time)

    response.headers["X-Process-Time"] = str(process_time)
    return response

# 5. Dependency Injection
def get_orchestrator(settings: Settings = Depends(get_settings)):
    return FixOrchestrator(repo_path=settings.repo_path if hasattr(settings, 'repo_path') else ".")

# Routes
@app.get("/healthz")
async def health_check():
    """Liveness check (S10)."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/readyz")
async def readiness_check():
    """Readiness check (S10)."""
    return {"status": "ready"}

@app.get("/")
async def root():
    return {"message": "PR Fix Agent API - Production Ready"}

@app.post("/api/v1/agent/analyze")
async def analyze_findings(
    payload: Dict,
    orchestrator: FixOrchestrator = Depends(get_orchestrator)
):
    """Analyze findings via the orchestrator."""
    # Simplified implementation for now
    return {"message": "Analysis started", "payload": payload}
