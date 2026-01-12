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
 feat/complete-10268506225633119435
import asyncio

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request


from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
 feature/complete-orchestrator-and-scheduler-3340126171226885686
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.clients.kimi import KimiClient
from rainmaker_orchestrator.core.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.config import settings

# Configure logging
logging.basicConfig(
 feat/complete-10268506225633119435
    level=getattr(logging, settings.log_level.upper(), logging.INFO),

    level=getattr(logging, settings.log_level),
 feature/complete-orchestrator-and-scheduler-3340126171226885686
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
 feat/complete-10268506225633119435
    context: str = Field(..., description="Task description or prompt")
    type: Optional[str] = Field(default="coding_task", description="Task type")
    model: Optional[str] = Field(default=None, description="AI model to use")
    output_filename: Optional[str] = Field(default=None, description="Output filename for coding tasks")
    timeout: Optional[int] = Field(default=300, description="Timeout in seconds")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")


    task: str = Field(..., description="Task description or code to execute")
    mode: str = Field(default="general", description="Execution mode")
    timeout: Optional[int] = Field(default=300, description="Timeout in seconds")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")


 feature/complete-orchestrator-and-scheduler-3340126171226885686
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
 feat/complete-10268506225633119435
    workspace_status: str

 feature/complete-orchestrator-and-scheduler-3340126171226885686


# Application Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
 feat/complete-10268506225633119435
    Initializes services on startup and performs cleanup on shutdown.
    """
    logger.info("Starting Rainmaker Orchestrator...")



    Initializes services on startup and performs cleanup on shutdown.
    """
    # Startup
    logger.info("Starting Rainmaker Orchestrator...")

    # Initialize clients and agents
 feature/complete-orchestrator-and-scheduler-3340126171226885686
    app.state.kimi_client = KimiClient()
    app.state.orchestrator = RainmakerOrchestrator(workspace_path=settings.workspace_path)
    app.state.healer_agent = SelfHealingAgent(
        kimi_client=app.state.kimi_client,
        orchestrator=app.state.orchestrator
    )
    logger.info(f"Workspace directory: {settings.workspace_path}")

 feat/complete-10268506225633119435
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

    # Health check on startup
    if app.state.kimi_client.health_check():
        logger.info("Kimi client health check: PASS")
    else:
        logger.warning("Kimi client health check: FAIL - service may be degraded")

    logger.info("Rainmaker Orchestrator started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Rainmaker Orchestrator...")
    logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="Rainmaker Orchestrator",
    description="AI-powered orchestration system with self-healing capabilities",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Health and Status Endpoints
# ============================================================================

@app.get("/", tags=["Status"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Rainmaker Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        HealthResponse with service status information
    """
    try:
        kimi_healthy = app.state.kimi_client.health_check()
        orchestrator_healthy = hasattr(app.state, 'orchestrator')

        overall_status = "healthy" if (kimi_healthy and orchestrator_healthy) else "degraded"

        return HealthResponse(
            status=overall_status,
            services={
                "kimi": "up" if kimi_healthy else "down",
                "orchestrator": "up" if orchestrator_healthy else "down"
            },
            version="1.0.0",
            environment=settings.environment
        )
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=f"Health check failed: {e!r}")


@app.get("/metrics", response_class=PlainTextResponse, tags=["Status"])
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for monitoring and alerting.
    """
    uptime_seconds = int(time.time() - metrics["start_time"])

    # Prometheus text format
    output = []
    output.append("# HELP rainmaker_alerts_processed_total Total number of alerts processed")
    output.append("# TYPE rainmaker_alerts_processed_total counter")
    output.append(f"rainmaker_alerts_processed_total {metrics['alerts_processed']}")
    output.append("")

    output.append("# HELP rainmaker_hotfixes_generated_total Total number of hotfixes generated")
    output.append("# TYPE rainmaker_hotfixes_generated_total counter")
    output.append(f"rainmaker_hotfixes_generated_total {metrics['hotfixes_generated']}")
    output.append("")

    output.append("# HELP rainmaker_tasks_executed_total Total number of tasks executed")
    output.append("# TYPE rainmaker_tasks_executed_total counter")
    output.append(f"rainmaker_tasks_executed_total {metrics['tasks_executed']}")
    output.append("")

    output.append("# HELP rainmaker_uptime_seconds Uptime in seconds")
    output.append("# TYPE rainmaker_uptime_seconds gauge")
    output.append(f"rainmaker_uptime_seconds {uptime_seconds}")
    output.append("")

    return "\n".join(output)


# ============================================================================
# Alert Handling Endpoints
# ============================================================================

@app.post("/webhook/alert", tags=["Alerts"])
async def handle_alert_webhook(
    alert: AlertPayload,
    background_tasks: BackgroundTasks
):
    """
    Handle Prometheus Alert Manager webhooks.

    Receives critical alerts and triggers AI-powered hotfix generation.

    Args:
        alert: AlertPayload containing alert information
        background_tasks: FastAPI background tasks for async processing

    Returns:
        Dictionary with processing status and hotfix information
    """
    try:
        logger.info(f"Received alert for service: {alert.service}")
        metrics["alerts_processed"] += 1

        # Convert Pydantic model to dict for processing
        alert_dict = alert.model_dump()

        # Process alert
        result = app.state.healer_agent.handle_alert(alert_dict)

        if result.get("status") == "hotfix_generated":
            metrics["hotfixes_generated"] += 1

        logger.info(f"Alert processed: {result['status']}")

        return result

    except Exception as e:
        logger.exception(f"Failed to handle alert for {alert.service}")
        raise HTTPException(
            status_code=500,
            detail=f"Alert processing failed: {e!r}"
        )


@app.post("/alerts/batch", tags=["Alerts"])
async def handle_batch_alerts(alerts: List[AlertPayload]):
    """
    Handle multiple alerts in batch.

    Args:
        alerts: List of AlertPayload objects

    Returns:
        List of processing results for each alert
    """
    try:
        results = []

        for alert in alerts:
            alert_dict = alert.model_dump()
            result = app.state.healer_agent.handle_alert(alert_dict)
            results.append(result)
            metrics["alerts_processed"] += 1
            if result.get("status") == "hotfix_generated":
                metrics["hotfixes_generated"] += 1

        logger.info(f"Processed {len(alerts)} alerts in batch")

        return {
            "total": len(alerts),
            "results": results
        }

    except Exception as e:
        logger.exception("Failed to process batch alerts")
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {e!r}"
        )


# ============================================================================
# Task Execution Endpoints
# ============================================================================

@app.post("/execute", tags=["Execution"])
async def execute_task(request: ExecuteRequest):
    """
    Execute a task or code using the orchestrator.

    Args:
        request: ExecuteRequest with task details

    Returns:
        Execution result with output and status
    """
    if not request.task:
        raise HTTPException(status_code=422, detail="Task cannot be empty")
    try:
        logger.info(f"Executing task in {request.mode} mode")
        metrics["tasks_executed"] += 1

        # Execute task using orchestrator
        result = app.state.orchestrator.execute(
            task=request.task,
            mode=request.mode,
            timeout=request.timeout,
            environment=request.environment or {}
        )

        logger.info(f"Task execution completed: {result.get('status')}")

        return result

    except TimeoutError:
        logger.error(f"Task execution timeout after {request.timeout}s")
        raise HTTPException(
            status_code=408,
            detail=f"Task execution timeout after {request.timeout} seconds"
        )
    except Exception as e:
        logger.exception("Task execution failed")
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {e!r}"
        )


@app.post("/execute/async", tags=["Execution"])
async def execute_task_async(
    request: ExecuteRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a task asynchronously in the background.

    Note: Task ID tracking is not yet implemented. This is fire-and-forget.

    Args:
        request: ExecuteRequest with task details
        background_tasks: FastAPI background tasks

    Returns:
        Task ID (for future status tracking)
    """
    if not request.task:
        raise HTTPException(status_code=422, detail="Task cannot be empty")
    try:
        import uuid
        task_id = str(uuid.uuid4())

        logger.info(f"Queuing async task {task_id}")
        metrics["tasks_executed"] += 1

        # Add task to background queue
        background_tasks.add_task(
            app.state.orchestrator.execute,
            task=request.task,
            mode=request.mode,
            timeout=request.timeout,
            environment=request.environment or {}
        )

        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Task queued for execution (note: status tracking not implemented)"
        }

    except Exception as e:
        logger.exception("Failed to queue async task")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue task: {e!r}"
        )


# ============================================================================
# Workspace File Management Endpoints
# ============================================================================

@app.get("/workspace/files", tags=["Workspace"])
async def list_workspace_files(path: str = ""):
    """
    List files in the workspace directory.

    Args:
        path: Optional subdirectory path within workspace

    Returns:
        List of files and directories
    """
    try:
        workspace_path = Path(settings.workspace_path) / path

        if not workspace_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")

        if not workspace_path.is_relative_to(settings.workspace_path):
            raise HTTPException(status_code=403, detail="Access denied")

        files = []
        for item in workspace_path.iterdir():
            files.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": item.stat().st_mtime
            })

        return {
            "path": str(path),
            "files": files,
            "count": len(files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list workspace files at {path}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {e!r}"
        )


@app.post("/workspace/upload", response_model=FileUploadResponse, tags=["Workspace"])
async def upload_workspace_file(
    file: UploadFile = File(...),
    path: str = ""
):
    """
    Upload a file to the workspace.

    Args:
        file: File to upload
        path: Optional subdirectory path within workspace

    Returns:
        FileUploadResponse with upload details
    """
    try:
        workspace_path = Path(settings.workspace_path) / path
        workspace_path.mkdir(parents=True, exist_ok=True)

        file_path = workspace_path / file.filename

        if not file_path.is_relative_to(settings.workspace_path):
            raise HTTPException(status_code=403, detail="Access denied")

        # Write file
        content = await file.read()
        file_path.write_bytes(content)

        logger.info(f"File uploaded: {file_path}")

        return FileUploadResponse(
            filename=file.filename,
            path=str(file_path.relative_to(settings.workspace_path)),
            size=len(content),
            status="uploaded"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to upload file {file.filename}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {e!r}"
        )
 feature/complete-orchestrator-and-scheduler-3340126171226885686

# Other endpoints from the feat/complete branch can be added here, adapting them to use the app.state objects
# ... (handle_alert_webhook, execute_task, workspace endpoints etc.)

 feat/complete-10268506225633119435
# ============================================================================
# Application Entry Point
# ============================================================================


@app.get("/workspace/download/{file_path:path}", tags=["Workspace"])
async def download_workspace_file(file_path: str):
    """
    Download a file from the workspace.

    Args:
        file_path: Path to file within workspace

    Returns:
        FileResponse with the requested file
    """
    try:
        full_path = Path(settings.workspace_path) / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not full_path.is_relative_to(settings.workspace_path):
            raise HTTPException(status_code=403, detail="Access denied")

        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to download file {file_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {e!r}"
        )


@app.delete("/workspace/delete/{file_path:path}", tags=["Workspace"])
async def delete_workspace_file(file_path: str):
    """
    Delete a file from the workspace.

    Args:
        file_path: Path to file within workspace

    Returns:
        Deletion confirmation
    """
    try:
        full_path = Path(settings.workspace_path) / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not full_path.is_relative_to(settings.workspace_path):
            raise HTTPException(status_code=403, detail="Access denied")

        if full_path.is_file():
            full_path.unlink()
        elif full_path.is_dir():
            import shutil
            shutil.rmtree(full_path)

        logger.info(f"Deleted: {full_path}")

        return {
            "status": "deleted",
            "path": file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete {file_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {e!r}"
        )


@app.post("/workspace/create-directory", tags=["Workspace"])
async def create_workspace_directory(path: str):
    """
    Create a directory in the workspace.

    Args:
        path: Directory path to create

    Returns:
        Creation confirmation
    """
    try:
        dir_path = Path(settings.workspace_path) / path

        if not dir_path.is_relative_to(settings.workspace_path):
            raise HTTPException(status_code=403, detail="Access denied")

        dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created directory: {dir_path}")

        return {
            "status": "created",
            "path": path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create directory {path}")
        raise HTTPException(
            status_code=500,
            detail=f"Directory creation failed: {e!r}"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    logger.exception("Internal server error")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": str(request.url)
        }
    )


# ============================================================================
# Application Entry Point
# ============================================================================

 feature/complete-orchestrator-and-scheduler-3340126171226885686
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
 feat/complete-10268506225633119435
        "rainmaker_orchestrator.server:app",

        "server:app",
 feature/complete-orchestrator-and-scheduler-3340126171226885686
        host="0.0.0.0",
        port=8080,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
