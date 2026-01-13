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

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.clients.kimi import KimiClient
from rainmaker_orchestrator.core.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
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
    task: str = Field(..., description="Task description or code to execute")
    mode: str = Field(default="general", description="Execution mode")
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


# Application Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application's startup and shutdown lifecycle.
    
    On startup, attaches a KimiClient to `app.state.kimi_client`, initializes a RainmakerOrchestrator using `settings.workspace_path` and assigns it to `app.state.orchestrator`, and creates a SelfHealingAgent assigned to `app.state.healer_agent`. Performs an initial health check of the Kimi client. Yields control for the running application and completes shutdown after the yield.
    """
    # Startup
    logger.info("Starting Rainmaker Orchestrator...")

    # Initialize clients and agents
    app.state.kimi_client = KimiClient()
    app.state.orchestrator = RainmakerOrchestrator(workspace_path=settings.workspace_path)
    app.state.healer_agent = SelfHealingAgent(
        kimi_client=app.state.kimi_client,
        orchestrator=app.state.orchestrator
    )
    logger.info(f"Workspace directory: {settings.workspace_path}")

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
    """
    Return basic API information and root endpoints for the service.
    
    Returns:
        dict: Mapping with keys 'service', 'version', 'status', 'docs', and 'health'.
    """
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
    Return the application's health status for load balancers and monitoring.
    
    Performs checks for the Kimi client and the orchestrator presence and returns a HealthResponse whose top-level
    `status` is "healthy" when both services are available and "degraded" otherwise. The `services` mapping uses
    "up" or "down" for each service and `environment` reflects current settings.
    
    Returns:
        HealthResponse: Overall health, per-service statuses, version, and environment.
    
    Raises:
        HTTPException: with status code 503 if an internal error occurs during the health check.
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
    Expose Prometheus-formatted metrics for the application.
    
    Metrics include total alerts processed, hotfixes generated, tasks executed, and uptime in seconds.
    
    Returns:
        metrics_text (str): Plaintext in Prometheus exposition format containing counters for alerts, hotfixes, tasks and a gauge for uptime.
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
    Handle a single Prometheus Alertmanager webhook and trigger AI-driven hotfix generation when applicable.
    
    Parameters:
        alert (AlertPayload): Incoming alert data with service, description, severity, labels, and annotations.
    
    Returns:
        result (dict): Processing outcome containing at least a `status` key (e.g., `"hotfix_generated"`, `"no_action"`) and, when applicable, additional hotfix information under keys such as `hotfix` or `details`.
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
    Process a list of alert payloads and return per-alert processing results.
    
    Parameters:
        alerts (List[AlertPayload]): Alerts to process; each alert will be converted to a dict and handled by the configured healer agent.
    
    Returns:
        dict: A summary containing `total` (int) number of alerts processed and `results` (List[dict]) with the healer agent's result for each alert.
    
    Raises:
        HTTPException: If any unexpected error occurs while processing the batch, an HTTP 500 error is raised with failure details.
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
    
    Parameters:
        request (ExecuteRequest): Execution parameters including:
            - task: the command or code to run
            - mode: execution mode (e.g., "shell", "python")
            - timeout: maximum execution time in seconds
            - environment: environment variables to provide to the task
    
    Returns:
        dict: Execution result containing at least a `status` field and any output or metadata produced by the orchestrator.
    
    Raises:
        HTTPException: 422 if `request.task` is empty.
        HTTPException: 408 if execution times out after `request.timeout` seconds.
        HTTPException: 500 if execution fails for any other reason.
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
    Queue a task for background execution.
    
    Validates that the request contains a non-empty task, schedules the orchestrator to execute it via FastAPI's BackgroundTasks, and increments execution metrics.
    
    Parameters:
        request (ExecuteRequest): Task details including `task`, `mode`, `timeout`, and optional `environment`.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks instance used to schedule the execution.
    
    Returns:
        dict: A dictionary with keys:
            - `task_id` (str): A UUID string identifying the queued task.
            - `status` (str): The string "queued".
            - `message` (str): A human-readable note about the queued task.
    
    Raises:
        HTTPException: If `request.task` is empty (422) or if scheduling the task fails (500).
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
    List files and directories within the configured workspace, optionally under a given subpath.
    
    Parameters:
        path (str): Relative subpath inside the workspace to list; empty string lists the workspace root.
    
    Returns:
        dict: {
            "path": str,                 # the requested relative path
            "files": [                   # list of entries in the directory
                {
                    "name": str,         # filename or directory name
                    "type": "file"|"directory",
                    "size": int,        # file size in bytes (0 for directories)
                    "modified": float   # last modification time as POSIX timestamp
                },
                ...
            ],
            "count": int                 # number of entries in "files"
        }
    
    Raises:
        HTTPException: 404 if the requested path does not exist.
        HTTPException: 403 if the requested path is outside the workspace.
        HTTPException: 500 for other failures while listing files.
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
    Store an uploaded file into the orchestrator workspace.
    
    Parameters:
        file (UploadFile): The file uploaded in the request.
        path (str): Subdirectory inside the workspace where the file will be written; interpreted relative to the workspace root.
    
    Returns:
        FileUploadResponse: Metadata for the stored file including filename, path relative to workspace, size in bytes, and status.
    
    Raises:
        HTTPException: 403 if the target path is outside the workspace, 500 if the upload or file write fails.
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


@app.get("/workspace/download/{file_path:path}", tags=["Workspace"])
async def download_workspace_file(file_path: str):
    """
    Provide a FileResponse for a file located inside the configured workspace.
    
    Parameters:
        file_path (str): Path to the file relative to the workspace root.
    
    Returns:
        FileResponse: Response that streams the requested file with filename set to the file's basename and media type 'application/octet-stream'.
    
    Raises:
        HTTPException: 404 if the file does not exist.
        HTTPException: 403 if the resolved path is outside the workspace.
        HTTPException: 400 if the path exists but is not a file.
        HTTPException: 500 for unexpected server errors during preparation of the response.
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
    Delete a file or directory located under the configured workspace.
    
    Parameters:
        file_path (str): Path relative to the workspace root to delete.
    
    Returns:
        dict: Confirmation object with keys `status` (always `"deleted"`) and `path` (the provided `file_path`).
    
    Raises:
        HTTPException: 404 if the path does not exist; 403 if the path is outside the workspace; 500 for other deletion failures.
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
    Create a directory under the configured workspace path.
    
    Ensures the provided path is inside the application's workspace and creates the directory (including parents) if it does not exist.
    
    Parameters:
        path (str): Relative directory path to create inside the workspace.
    
    Returns:
        dict: A mapping with `status` set to `"created"` and `path` echoing the requested path.
    
    Raises:
        HTTPException: Raised with status 403 if the path is outside the workspace, or 500 if directory creation fails.
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
    """
    Handle requests to missing endpoints by returning a JSON 404 response.
    
    Parameters:
        request: The incoming request; its URL is included in the response `path`.
        exc: The exception raised for the missing route.
    
    Returns:
        JSONResponse: A response with `error` ("Not Found"), a human-readable `message`, and the request `path`.
    """
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
    """
    Handle internal server errors and return a standardized JSON 500 response.
    
    Parameters:
        request (Request): The incoming HTTP request; its URL is included in the response.
        exc (Exception): The exception that triggered this handler.
    
    Returns:
        JSONResponse: HTTP 500 response with a JSON body containing "error", "message", and "path".
    """
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )