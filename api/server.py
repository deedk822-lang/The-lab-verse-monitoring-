import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
import opik

# Internal Imports
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api")

class ExecuteTaskPayload(BaseModel):
    type: str
    context: str
    model: Optional[str] = None
    output_filename: Optional[str] = None

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Manage lifecycle of the Authority Engine.\"\"\"
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    logger.info("Authority Engine initialized and ready.")
    yield
    await orchestrator.aclose()
    logger.info("Authority Engine shut down.")

app = FastAPI(
    title="Rainmaker Authority API",
    description="The secure gateway for the 4-Judge Authority Engine.",
    version="1.1.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {
        "status": "connected",
        "engine": "Authority Engine v1.1",
        "features": ["4-Judge Flow", "Self-Healing", "Opik Telemetry"]
    }

@app.post("/webhook/hubspot")
async def hubspot_webhook(payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks, request: Request):
    \"\"\"Asynchronous entry point for HubSpot events.\"\"\"
    orchestrator = request.app.state.orchestrator
    # Use model_dump() for Pydantic v2 compatibility
    background_tasks.add_task(orchestrator.run_authority_flow, payload.model_dump())
    return {"status": "accepted", "message": "Authority Flow queued."}

@app.post("/execute")
async def execute(payload: ExecuteTaskPayload, request: Request):
    \"\"\"Synchronous execution for direct agent tasks.\"\"\"
    orchestrator = request.app.state.orchestrator
    try:
        result = await orchestrator.execute_task(payload.model_dump())
        return result
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
