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
    Manage application startup and shutdown.

    Initializes services on startup and performs cleanup on shutdown.
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
    Provide basic API metadata for the service.
    
    Returns:
        info (dict): Mapping with keys:
            - service: Service name.
            - version: API version string.
            - status: Current service status.
            - docs: Path to API documentation.
            - health: Path to health endpoint.
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
    Health check endpoint that reports overall and per-service health for monitoring and load balancers.
    
    Returns:
        HealthResponse: overall status ("healthy" or "degraded"), a `services` map with `kimi` and `orchestrator` statuses ("up" or "down"), `version`, and `environment`.
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
    Expose service runtime metrics formatted for Prometheus scraping.
    
    Returns:
        prometheus_text (str): Plain-text containing Prometheus metrics (alerts processed, hotfixes generated, tasks executed, and uptime in seconds).
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
    Process a Prometheus Alertmanager webhook payload and trigger remediation via the healer agent.
    
    Increments alert metrics and returns the healer agent's processing result.
    
    Parameters:
        alert (AlertPayload): Alert payload with service, description, severity, and optional labels/annotations.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks instance for scheduling any asynchronous work.
    
    Returns:
        dict: Processing result from the healer agent. The `status` key indicates the outcome (for example, `hotfix_generated`) and the dict may include hotfix details.
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
    Process a list of AlertPayloads and return per-alert processing results and a total count.
    
    Returns:
        dict: Dictionary with:
            - total (int): number of alerts processed.
            - results (List[Dict]): processing result for each alert. Each result may include a `status` key; a value of `"hotfix_generated"` indicates a hotfix was produced.
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
    Execute a task using the orchestrator.
    
    Returns:
        dict: Execution result containing outcome details such as `status` and `output`.
    """
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
    Queue a task for execution in the background and return a generated task identifier.
    
    Queues the provided ExecuteRequest to run via the orchestrator and returns a dictionary containing `task_id`, `status`, and `message`. Note: task status tracking is not implemented — the task is fire-and-forget after queuing.
    
    Parameters:
        request (ExecuteRequest): Task definition including `task`, `mode`, optional `timeout`, and optional `environment`.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks instance used to schedule the work.
    
    Returns:
        dict: Dictionary with keys:
            - task_id (str): Generated UUID for the queued task.
            - status (str): Current queue status, typically "queued".
            - message (str): Human-readable note about queuing and tracking.
    
    Raises:
        HTTPException: If the task cannot be queued.
    """
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
    List entries in the application's workspace or a subdirectory.
    
    Parameters:
        path (str): Relative subpath within the configured workspace to list; empty string lists the workspace root.
    
    Returns:
        dict: Object containing:
            - path (str): the requested relative path,
            - files (List[dict]): entries with keys `name`, `type` ("file" or "directory"), `size` (bytes, 0 for directories), and `modified` (epoch seconds),
            - count (int): number of entries returned.
    
    Raises:
        HTTPException: with status 404 if the requested path does not exist,
                       with status 403 if the requested path is outside the workspace,
                       with status 500 for other failures while reading the filesystem.
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
    Save an uploaded file into the configured workspace and return metadata about the stored file.
    
    Parameters:
        file (UploadFile): The uploaded file to save.
        path (str): Optional subdirectory under the workspace where the file will be stored.
    
    Returns:
        FileUploadResponse: Metadata for the stored file including `filename`, relative `path` within the workspace, `size` in bytes, and `status`.
    
    Raises:
        HTTPException: `403` if the target path is outside the workspace, `500` if the upload or write operation fails.
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
    Download a file from the configured workspace and return it as a FileResponse.
    
    Parameters:
        file_path (str): Relative path to the file inside the configured workspace.
    
    Returns:
        FileResponse: The file response for the requested file.
    
    Raises:
        HTTPException: 404 if the file does not exist, 403 if the path is outside the workspace, 400 if the path is not a file, 500 for other failures.
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
    Delete a file or directory located under the configured workspace path.
    
    Parameters:
        file_path (str): Relative path inside the workspace to the file or directory to delete.
    
    Returns:
        dict: Deletion confirmation with keys `"status": "deleted"` and `"path"` set to the provided `file_path`.
    
    Raises:
        HTTPException: 404 if the target does not exist.
        HTTPException: 403 if the resolved path is outside the workspace.
        HTTPException: 500 if deletion fails due to an internal error.
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
    
    Parameters:
        path (str): Relative path within the workspace to create.
    
    Returns:
        dict: {"status": "created", "path": <path>} confirming creation.
    
    Raises:
        HTTPException: 403 if the resolved path is outside the workspace.
        HTTPException: 500 if directory creation fails.
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
    Handle 404 (Not Found) errors by returning a JSON response with error details.
    
    Returns:
        JSONResponse: JSON object with keys:
          - `error`: short error code, `"Not Found"`.
          - `message`: human-readable message explaining the error.
          - `path`: the requested URL path that was not found.
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
    Handle uncaught exceptions and return a standardized 500 JSON response.
    
    Parameters:
        request: The incoming Starlette/FastAPI request object that triggered the error.
        exc: The exception instance that was raised.
    
    Returns:
        JSONResponse: A response with status code 500 and a JSON body containing `error`, `message`, and `path` fields describing the internal server error.
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