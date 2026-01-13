import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
import openlit

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
    """Manage lifecycle of the Authority Engine."""
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
    """Health check endpoint."""
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
    """Asynchronous entry point for HubSpot webhook events."""
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
    """Synchronous execution endpoint for direct agent tasks."""
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
