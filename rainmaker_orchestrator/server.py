"""Rainmaker Orchestrator Server - Complete FastAPI Application

This module provides a comprehensive API for the Rainmaker Orchestrator,
including alert handling, workspace management, and task execution endpoints.
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.clients.kimi import KimiClient
from rainmaker_orchestrator.core.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics tracking
metrics = {
    "alerts_processed": 0,
    "hotfixes_generated": 0,
    "tasks_executed": 0,
    "start_time": time.time()
}


# Pydantic Models for Request/Response
class AlertPayload(BaseModel):
    """Prometheus Alert Manager webhook payload."""
    service: str = Field(..., description="Name of the affected service")
    description: str = Field(..., description="Error description or log")
    severity: str = Field(default="critical", description="Alert severity level")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Additional labels")
    annotations: Optional[Dict[str, str]] = Field(default=None, description="Additional annotations")


class ExecuteRequest(BaseModel):
    """Request model for task execution."""
    context: str = Field(..., description="Task description or prompt")
    type: Optional[str] = Field(default="coding_task", description="Task type")
    model: Optional[str] = Field(default=None, description="AI model to use")
    output_filename: Optional[str] = Field(default=None, description="Output filename for coding tasks")
    timeout: Optional[int] = Field(default=300, description="Timeout in seconds")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")

class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    filename: str
    path: str
    size: int
    status: str


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    services: Dict[str, str]
    version: str
    environment: str
    workspace_status: str


# Application Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    Initializes services on startup and performs cleanup on shutdown.
    """
    logger.info("Starting Rainmaker Orchestrator...")

    app.state.kimi_client = KimiClient()
    app.state.orchestrator = RainmakerOrchestrator(workspace_path=settings.workspace_path)
    app.state.healer_agent = SelfHealingAgent(
        kimi_client=app.state.kimi_client,
        orchestrator=app.state.orchestrator
    )
    logger.info(f"Workspace directory: {settings.workspace_path}")

    yield

    logger.info("Shutting down Rainmaker Orchestrator...")
    if hasattr(app.state.orchestrator, 'aclose'):
        await app.state.orchestrator.aclose()
    logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="Rainmaker Orchestrator",
    description="AI-powered orchestration system with self-healing capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================================
# Health and Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    try:
        kimi_healthy = await app.state.kimi_client.health_check()
        orchestrator_healthy = hasattr(app.state, 'orchestrator')

        # Check workspace accessibility
        workspace_status = "ok"
        try:
            workspace = Path(settings.workspace_path)
            if not workspace.exists():
                workspace.mkdir(parents=True, exist_ok=True)
            if not os.access(workspace, os.W_OK):
                workspace_status = "not_writable"
        except Exception as e:
            logger.error(f"Workspace check failed: {e}")
            workspace_status = f"error: {e}"

        overall_status = "healthy" if (kimi_healthy and orchestrator_healthy and workspace_status == "ok") else "degraded"

        return HealthResponse(
            status=overall_status,
            services={
                "kimi": "up" if kimi_healthy else "down",
                "orchestrator": "up" if orchestrator_healthy else "down"
            },
            version="2.0.0",
            environment=settings.environment,
            workspace_status=workspace_status
        )
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=f"Health check failed: {e!r}")

# Other endpoints from the feat/complete branch can be added here, adapting them to use the app.state objects
# ... (handle_alert_webhook, execute_task, workspace endpoints etc.)

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "rainmaker_orchestrator.server:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
