"""
Standalone server module for rainmaker orchestrator.
This file maintains backward compatibility with existing deployments.
For new implementations, use api/server.py instead.
"""
import logging
from fastapi import FastAPI

logger: logging.Logger = logging.getLogger("server")

app: FastAPI = FastAPI(
    title="Rainmaker Orchestrator Legacy Server",
    version="1.2.0",
    description="Legacy endpoint - use api/server.py for new deployments",
)


@app.get("/health")
async def health() -> dict:
    """Health check for legacy compatibility."""
    logger.warning("Legacy /health endpoint called - migrate to api/server.py")
    return {"status": "legacy", "message": "Use api/server.py for new deployments"}
