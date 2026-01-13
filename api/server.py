import os
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

app = FastAPI(title="Rainmaker Authority API", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "connected", "engine": "Authority Engine v1.0"}

@app.post("/webhook/hubspot")
async def hubspot_webhook(payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks, request: Request):
    """Entry point for the Authority Engine."""
    orchestrator = request.app.state.orchestrator
    
    # Trigger the Authority/Judge process
    background_tasks.add_task(orchestrator.run_authority_flow, payload.model_dump())
    
    return {"status": "accepted", "message": "Authority Flow initiated."}

@app.post("/execute")
async def execute(payload: ExecuteTaskPayload, request: Request):
    return await request.app.state.orchestrator.execute_task(payload.model_dump())
