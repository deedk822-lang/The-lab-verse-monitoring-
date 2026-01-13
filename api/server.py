from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest
import logging
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

request_count = Counter('http_requests_total', 'Total requests')
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator = RainmakerOrchestrator()
    yield
    await app.state.orchestrator.aclose()

app = FastAPI(title="Lab Verse Unified API", lifespan=lifespan)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    with request_duration.time():
        return await call_next(request)

@app.get("/health")
async def health(): return {"status": "healthy", "architecture": "4-Judge Authority Engine"}

@app.get("/metrics")
async def metrics(): return Response(generate_latest(), media_type="text/plain")

@app.post("/webhook/hubspot")
async def hubspot(payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks, request: Request):
    background_tasks.add_task(request.app.state.orchestrator.run_authority_flow, payload.model_dump())
    return {"status": "accepted", "message": "Flow initiated."}
