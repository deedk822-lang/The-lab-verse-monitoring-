import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import openlit
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

# Configure logging with structured format for Datadog
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger: logging.Logger = logging.getLogger("api")


class ExecuteTaskPayload(BaseModel):
    """Task execution request payload."""
    type: str = Field(..., description="Task type: authority_task or coding_task")
    context: str = Field(..., description="Task context and requirements")
    model: Optional[str] = Field(None, description="Override default model selection")
    output_filename: Optional[str] = Field(None, description="Output file for coding tasks")


class HubSpotWebhookPayload(BaseModel):
    """HubSpot webhook event payload."""
    objectId: int = Field(..., description="HubSpot contact or deal ID")
    message_body: str = Field(..., description="Event message content")


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """
    Manage application startup and shutdown for the Authority Engine.

    On startup, conditionally initialize OpenLIT telemetry (skipped when the environment variable CI is "true") using the OPENLIT_OTLP_ENDPOINT and ENVIRONMENT environment variables, instantiate a RainmakerOrchestrator, and attach it to app.state.orchestrator. On shutdown, close the orchestrator by calling its aclose() coroutine.
    """
    # Initialize OpenLIT only if not in CI environment
    if os.getenv("CI") != "true":
        try:
            openlit.init(
                otlp_endpoint=os.getenv(
                    "OPENLIT_OTLP_ENDPOINT",
                    "https://otlp.datadoghq.com:4318"
                ),
                application_name="rainmaker-orchestrator",
                environment=os.getenv("ENVIRONMENT", "production"),
            )
            logger.info("OpenLIT telemetry initialized")
        except Exception as e:
            logger.warning(f"OpenLIT initialization warning: {e}")

    orchestrator: RainmakerOrchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    logger.info("✅ Authority Engine initialized and ready")

    yield

    await orchestrator.aclose()
    logger.info("🛑 Authority Engine shut down gracefully")


app: FastAPI = FastAPI(
    title="Rainmaker Authority API",
    description="Secure gateway for the 4-Judge Authority Engine",
    version="1.2.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
async def health() -> dict:
    """
    Report application health status and available engine features.

    Returns:
        dict: A status payload with keys:
            - "status" (str): overall connectivity state, e.g. "connected".
            - "engine" (str): engine name and version.
            - "features" (list[str]): list of enabled feature names.
    """
    return {
        "status": "connected",
        "engine": "Authority Engine v1.2",
        "features": ["4-Judge Flow", "Self-Healing", "Opik Telemetry", "SSRF Protection"],
    }


@app.post("/webhook/hubspot", tags=["Webhooks"])
async def hubspot_webhook(
    payload: HubSpotWebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
) -> dict:
    """
    Enqueues an authority flow run for an incoming HubSpot webhook event.

    Parameters:
        payload (HubSpotWebhookPayload): HubSpot event payload containing `objectId` and `message_body`.

    Returns:
        dict: A response with status and human-readable message, e.g. `{"status": "accepted", "message": "Authority Flow queued"}`.

    Raises:
        HTTPException: Raised with status code 500 when webhook processing fails.
    """
    try:
        orchestrator: RainmakerOrchestrator = request.app.state.orchestrator
        background_tasks.add_task(
            orchestrator.run_authority_flow,
            payload.model_dump(),
        )
        logger.info(f"HubSpot event queued: contact_id={payload.objectId}")
        return {"status": "accepted", "message": "Authority Flow queued"}
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@app.post("/execute", tags=["Tasks"])
async def execute(payload: ExecuteTaskPayload, request: Request) -> dict:
    """
    Execute a direct agent task using the application's orchestrator.

    Calls the orchestrator attached to the FastAPI app state with the provided payload and returns the orchestrator's result.

    Returns:
        dict: The task execution result dictionary (typically includes a 'status' key).

    Raises:
        HTTPException: Raised with status 400 when payload validation fails, or status 500 for other execution errors.
    """
    try:
        orchestrator: RainmakerOrchestrator = request.app.state.orchestrator
        result: dict = await orchestrator.execute_task(payload.model_dump())
        logger.info(f"Task executed: type={payload.type}, status={result.get('status')}")
        return result
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Task execution failed")
