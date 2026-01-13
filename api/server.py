import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel

# Internal Imports
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ExecuteTaskPayload(BaseModel):
    type: str
    context: str
    model: Optional[str] = None

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    yield
    await orchestrator.aclose()

app = FastAPI(title="Rainmaker Impact API", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "connected", "engine": "Autonomous Authority v2.0"}

@app.post("/webhook/hubspot")
async def hubspot_webhook(payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks, request: Request):
    """Entry point for the Autonomous Loop."""
    orchestrator = request.app.state.orchestrator
    
    # Process the 'Impact Engine' in the background to avoid HubSpot timeouts
    background_tasks.add_task(orchestrator.trigger_impact_engine, payload.model_dump())
    
    return {"status": "accepted", "message": "Impact Engine triggered."}

@app.post("/execute")
async def execute(payload: ExecuteTaskPayload, request: Request):
    return await request.app.state.orchestrator.execute_task(payload.model_dump())
