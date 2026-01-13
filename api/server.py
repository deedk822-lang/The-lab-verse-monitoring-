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

 coderabbitai/docstrings/52d56b6
    from rainmaker_orchestrator import RainmakerOrchestrator
 feat/architectural-improvements-9809589759324023108-13552811548169517820
    print(f"✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    print(f"❌ Import error in server: {e}. Using a dummy class for tests.")
    # This allows tests to import the module and mock the orchestrator
    class RainmakerOrchestrator:
        def __init__(self):
            """
            Create a fallback RainmakerOrchestrator instance with an empty, mutable `config` dictionary.
            
            The `config` attribute is initialized as an empty dict and may be populated at runtime to provide settings (for example, access tokens or other integration parameters).
            """
            self.config = {}
        async def _call_ollama(self, *args, **kwargs):
            """
            Provide a fallback implementation that simulates an Ollama call when no real orchestrator is available.
            
            Returns:
                dict: An empty dictionary (`{}`) used as a placeholder response.
            """
            return {}

@app.post("/execute")
 feature/elite-ci-cd-pipeline-1070897568806221897
@limiter.limit("10/minute")
async def execute_task(
    task_request: ExecuteRequest,
    request: Request,
    orchestrator: RainmakerOrchestrator = Depends(get_orchestrator)
):
    """Executes a task, with OpenLIT tracing."""
    task_id = request.headers.get("X-Request-ID", "unknown")
=======
async def execute_task(payload: ExecuteTaskPayload, request: Request):
    """Execute a task using the Rainmaker Orchestrator."""
    result = await request.app.state.orchestrator.execute_task(payload.model_dump())
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("message", "Task execution failed"))
    return result
 main

 main

@app.get("/intel/market")
async def get_market_intel(company: str):
    """
 coderabbitai/docstrings/52d56b6
    Manage application lifespan by initializing a RainmakerOrchestrator on startup and closing it on shutdown.
    
    Instantiates RainmakerOrchestrator and assigns it to app.state.orchestrator when the app starts. On shutdown, calls the orchestrator's aclose() method to perform graceful cleanup of resources.
    """
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    yield
    # Shutdown
    await orchestrator.aclose()

app = FastAPI(title="Lab Verse API", lifespan=lifespan)
 main

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str
    subscriptionType: Optional[str] = None

@app.get("/health")
async def health_check():
    """
    Return the current service health status.
    
    Returns:
        dict: A mapping with the key "status" set to the string "healthy".
    """
    return {"status": "healthy"}

 coderabbitai/docstrings/52d56b6
 feat/architectural-improvements-9809589759324023108-13552811548169517820
@app.get("/intel/market")
async def get_market_intel(company: str):

 """
 Fetches market intelligence for the given company name.
 
 Parameters:
     company (str): The company name to retrieve market intelligence for.
 
 Returns:
     dict: A payload containing market intelligence fields such as:
         - source (str): Data source identifier.
         - company (str): Echoed company name.
         - status (str): High-level market status (e.g., "stable", "rising", "declining").
         - timestamp (str): ISO-8601 timestamp when the intelligence was generated.
 """
 feat/modernize-python-stack-2026-3829493454699415671
@app.get("/intel/market")
async def get_market_intel_endpoint(company_name: str):
    """
    Return market intelligence for the given company name.
    
    Returns:
        A mapping containing market intelligence for the company, typically including keys such as `source`, `company`, `status`, and `timestamp`.
    """
    data = get_market_intel(company_name)
    return JSONResponse(content=data)

# TODO: Replace this with a real market intelligence API (e.g., Perplexity, Google Search)
 main

# Placeholder implementation - tracked separately for production replacement
 main
def get_market_intel(company_name: str):
 """
 Return a simulated market intelligence payload for the given company.
 
 Parameters:
     company_name (str): Name or identifier of the company to query.
 
 Returns:
     dict: Structured placeholder market intelligence containing:
         - source (str): Data source label (simulated).
         - company (str): Echo of the queried company name.
         - status (str): Integration or data-status message.
         - timestamp (float): Unix epoch timestamp of the response.
         - latest_headline (str): Representative recent headline (simulated).
         - financial_health_signal (str): High-level financial health assessment (simulated).
         - key_pain_point (str): Primary operational/strategic challenge inferred (simulated).
         - sales_hook (str): Suggested outreach angle or positioning based on the simulated intel.
 """
 main

    Return a simulated market intelligence report for the specified company.
    
    Parameters:
        company (str): The company name to retrieve market intelligence for.
    
    Returns:
        dict: A structured market intelligence object with keys:
            - source (str): The data source label (simulated).
            - company (str): Echoes the requested company name.
            - status (str): Integration/configuration status or note.
            - timestamp (float): Unix timestamp of the report generation.
 main
    """
    logging.info(f"Fetching market intel for (placeholder): {company}")
    return {
        "source": "Live Search (Simulated)",
        "company": company,
        "status": "Integration Pending - Configure Perplexity/Google API",
        "timestamp": time.time()
    }

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(payload: HubSpotWebhookPayload):
    """
    Handle an incoming HubSpot webhook payload by validating that the HubSpot client is available.
 main
    
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
 feature/elite-ci-cd-pipeline-1070897568806221897
            raise HTTPException(status_code=500, detail="Task execution failed")

            logging.info(f"Successfully created and associated enriched deal {created_deal.id} for contact {contact_id}.")

    except Exception as e:
        logging.error(f"Error creating HubSpot deal for contact {contact_id}", exc_info=e)
        # Do not return a value, this is a background task

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(request: Request, payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks):
    """
    Enqueue processing of a HubSpot webhook payload to run in the background and acknowledge receipt.
    
    Returns:
        dict: `"status"` is `"accepted"`, `"contact_id"` is the HubSpot contact id from the payload.
    """
    background_tasks.add_task(process_webhook_data, payload, request.app)
 coderabbitai/docstrings/52d56b6
    return {"status": "accepted", "contact_id": payload.objectId}
 coderabbitai/docstrings/52d56b6
 main

 main
 main

    return {"status": "accepted", "contact_id": payload.objectId}
 main
 main
