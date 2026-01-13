import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from pydantic import BaseModel, Field, validator # type: ignore
from slowapi import Limiter # type: ignore
from slowapi.util import get_remote_address # type: ignore
from slowapi.errors import RateLimitExceeded # type: ignore

from src.rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
from src.rainmaker_orchestrator.agents.healer import SelfHealingAgent
from src.rainmaker_orchestrator.clients.kimi import KimiApiClient # type: ignore

# --- Observability & Logging ---
import openlit # type: ignore
import structlog # type: ignore
from prometheus_fastapi_instrumentator import Instrumentator # type: ignore

logger = structlog.get_logger(__name__)

# --- Application Setup ---
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage lifecycle of shared resources."""
    logger.info("Application startup: Initializing resources.")

    orchestrator = RainmakerOrchestrator()
    kimi_client = KimiApiClient()

    app.state.orchestrator = orchestrator
    app.state.kimi_client = kimi_client

    if os.getenv("OPENLIT_ENDPOINT"):
        openlit.init(
            otlp_endpoint=os.getenv("OPENLIT_ENDPOINT"),
            application_name="rainmaker-orchestrator"
        )
        logger.info("OpenLIT tracing initialized.")

    yield

    logger.info("Application shutdown: Cleaning up resources.")
    await orchestrator.aclose()
    await kimi_client.close()

app = FastAPI(
    title="Rainmaker Orchestrator API",
    version="3.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse({"error": "Rate limit exceeded"}, status_code=429))

# Instrument for Prometheus
Instrumentator().instrument(app).expose(app)


# --- Dependency Injection ---
async def get_orchestrator(request: Request) -> RainmakerOrchestrator:
    if not hasattr(request.app.state, 'orchestrator'):
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return request.app.state.orchestrator

async def get_kimi_client(request: Request) -> Optional[KimiApiClient]:
    return getattr(request.app.state, 'kimi_client', None)

# --- Pydantic Models ---
class HealthResponse(BaseModel):
    status: str
    dependencies: Dict[str, Dict[str, Any]]

class ExecuteRequest(BaseModel):
    context: str = Field(..., min_length=1, max_length=10000)
    type: str = "coding_task"
    model: Optional[str] = None
    output_filename: Optional[str] = None

    @validator('output_filename')
    def validate_filename(cls, v):
        if v and (".." in v or "/" in v or "\\" in v):
            raise ValueError("Path traversal attempt detected")
        return v

# --- API Endpoints ---
@app.get("/health", response_model=HealthResponse)
@limiter.limit("100/minute")
async def health_check(
    request: Request,
    orchestrator: RainmakerOrchestrator = Depends(get_orchestrator),
    kimi_client: Optional[KimiApiClient] = Depends(get_kimi_client)
) -> JSONResponse:
    """Provides a detailed health check of the API and its dependencies."""
    orchestrator_health = await orchestrator.health_check()
    kimi_health = await kimi_client.health_check() if kimi_client else {"status": "not_configured"}

    status = "healthy"
    if orchestrator_health["status"] != "healthy" or kimi_health["status"] != "healthy":
        status = "degraded"

    response_data = {
        "status": status,
        "dependencies": {
            "orchestrator": orchestrator_health,
            "kimi_client": kimi_health
        }
    }
    return JSONResponse(content=response_data)

@app.post("/execute")
@limiter.limit("10/minute")
async def execute_task(
    task_request: ExecuteRequest,
    request: Request,
    orchestrator: RainmakerOrchestrator = Depends(get_orchestrator)
):
    """Executes a task, with OpenLIT tracing."""
    task_id = request.headers.get("X-Request-ID", "unknown")
    
    with openlit.trace(
        name="execute_task",
        metadata={
            "task_id": task_id,
            "task_type": task_request.type,
            "model": task_request.model
        }
    ) as span:
        try:
            result = await orchestrator.execute_task(task_request.model_dump())
            span.set_attribute("response_length", len(str(result)))
            return result
        except Exception as e:
            logger.exception(
                "execute_task_failed",
                error=str(e),
                request_id=task_id
            )
            raise HTTPException(status_code=500, detail="Task execution failed")
