from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from datetime import datetime
import sys
import os
import json
import httpx
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput
from prometheus_client import Counter, Histogram, generate_latest
from pathlib import Path
import logging
import asyncio
import time

# --- Prometheus Metrics ---
request_count = Counter('http_requests_total', 'Total requests')
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

# --- Pydantic Models ---
class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

class AlertPayload(BaseModel):
    alert_name: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(warning|critical|info)$")
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "alert_name": "HighCPU",
                "severity": "critical",
                "timestamp": "2025-01-11T10:00:00Z"
            }
        }

# --- Configuration ---
DEAL_CREATION_INTENT_SCORE_THRESHOLD = 8
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
WORKSPACE_ROOT = Path("/app/workspace").resolve()

# Ensure the root directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
    logging.info("✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    logging.error(f"❌ Import error in server: {e}")
    logging.error(f"CWD: {os.getcwd()}")
    raise

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    """
    Manage the FastAPI application's startup and shutdown lifecycle resources.
    
    On startup, initializes and attaches a RainmakerOrchestrator instance to app.state.orchestrator and an httpx.AsyncClient to app.state.http_client. On shutdown, closes the http client to release network resources.
    
    Parameters:
        app (FastAPI): The FastAPI application whose state will be populated and cleaned up.
    """
    logging.info("🚀 Starting up the server...")
    app.state.orchestrator = RainmakerOrchestrator()
    app.state.http_client = httpx.AsyncClient()
    logging.info("✅ Server startup complete.")
    yield
    # Shutdown logic
    logging.info("🔌 Shutting down the server...")
    await app.state.http_client.aclose()
    logging.info("✅ Server shutdown complete.")

app = FastAPI(title="Lab Verse API", lifespan=lifespan)

# --- Middleware ---
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Increment the Prometheus request counter and measure the duration of the incoming HTTP request.
    
    Parameters:
        request (Request): The incoming FastAPI request.
        call_next (Callable): The downstream request handler to invoke with `request`.
    
    Returns:
        response (Response): The response produced by the downstream handler.
    """
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response

# --- Exception Handlers ---
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Handle ValueError exceptions by returning an HTTP 400 JSON response containing the error message.
    
    Parameters:
        exc (ValueError): The exception whose message will be returned in the response body.
    
    Returns:
        JSONResponse: A response with status code 400 and content {"detail": "<exception message>"}.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# --- Endpoints ---
@app.get("/health")
async def health_check():
    """
    Report service health.
    
    Returns:
        dict: Mapping with key "status" set to "healthy".
    """
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """
    Expose current Prometheus metrics in the Prometheus text exposition format.
    
    Returns:
        An HTTP Response containing the latest Prometheus metrics encoded in the Prometheus text exposition format with content type "text/plain".
    """
    return Response(generate_latest(), media_type="text/plain")

@app.get("/intel/market")
async def get_market_intel(company: str):
    """
    Provide a simulated market intelligence payload for the given company.
    
    Parameters:
        company (str): The company name to include in the simulated report.
    
    Returns:
        dict: A payload with keys:
            - `source`: human-readable source label for the simulated data.
            - `company`: the provided company name.
            - `status`: integration/setup status or notes for real intel providers.
            - `timestamp`: Unix epoch time (float) indicating when the payload was generated.
    """
    logging.info(f"Fetching market intel for (placeholder): {company}")
    return {
        "source": "Live Search (Simulated)",
        "company": company,
        "status": "Integration Pending - Configure Perplexity/Google API",
        "timestamp": time.time()
    }

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(request: Request, payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks):
    """
    Enqueue background processing for a HubSpot webhook payload.
    
    Schedules processing of the provided HubSpotWebhookPayload as a background task and returns an acceptance response.
    
    Returns:
        dict: A response containing `status` with value `"accepted"` and `contact_id` set to the webhook payload's `objectId`.
    """
    background_tasks.add_task(process_webhook_data, payload, request.app)
    return {"status": "accepted", "contact_id": payload.objectId}

async def process_webhook_data(payload: HubSpotWebhookPayload, app: FastAPI):
    """
    Process a HubSpot webhook payload by running an AI analysis, updating the contact with AI-derived properties, and creating/enriching a deal when intent is high.
    
    The function extracts contact ID and message text from `payload`, sends the text to the orchestrator's AI (Ollama) to obtain `company_name`, `summary`, `intent_score`, and `suggested_action`, then updates the HubSpot contact with those values. If `intent_score` exceeds the configured threshold, it fetches market intelligence, creates a new deal, and associates the deal with the contact. All external interactions (AI call, HubSpot API) are performed via services available on `app.state` and the function logs errors encountered during processing.
    
    Parameters:
        payload (HubSpotWebhookPayload): Incoming webhook data containing `objectId` (contact ID) and `message_body` (text to analyze).
        app (FastAPI): FastAPI application instance used to access orchestrator, configuration, and HTTP clients.
    """
    contact_id = payload.objectId
    chat_text = payload.message_body

    logging.info(f"Processing HubSpot webhook for contact: {contact_id}")

    try:
        prompt = f"Analyze this lead: {chat_text}. Identify the lead's company. Return ONLY JSON with keys: company_name, summary, intent_score (0-10), suggested_action."
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await app.state.orchestrator._call_ollama(ollama_task, {})

        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        logging.info(f"AI Analysis successful: {parsed_ai}")

        hubspot_access_token = app.state.orchestrator.config.get('HUBSPOT_ACCESS_TOKEN')
        if not hubspot_access_token:
            raise ValueError("HUBSPOT_ACCESS_TOKEN is not set.")

        client = HubSpot(access_token=hubspot_access_token)

        properties_to_update = {
            "ai_lead_summary": parsed_ai.get('summary', 'N/A'),
            "ai_buying_intent": parsed_ai.get('intent_score', 0),
            "ai_suggested_action": parsed_ai.get('suggested_action', 'N/A')
        }

        client.crm.contacts.basic_api.update(contact_id, {"properties": properties_to_update})
        logging.info(f"Successfully updated contact {contact_id} with AI analysis.")

        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            logging.info(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            intel_data = await get_market_intel(company_name)
            intel_status = intel_data.get('status', 'Market intel pending.')

            deal_properties = {
                "dealname": f"{company_name} - WhatsApp Lead",
                "pipeline": "default",
                "dealstage": "appointmentscheduled",
                "description": f"**AI WAR ROOM BRIEF:**\n\nMARKET INTEL: {intel_status}"
            }
            deal_input = SimplePublicObjectInput(properties=deal_properties)
            created_deal = client.crm.deals.basic_api.create(simple_public_object_input=deal_input)

            client.crm.deals.associations_api.create(
                deal_id=created_deal.id,
                to_object_type='contact',
                to_object_id=contact_id,
                association_type='deal_to_contact'
            )
            logging.info(f"Successfully created and associated enriched deal {created_deal.id} for contact {contact_id}.")

    except Exception as e:
        logging.error(f"Error processing HubSpot webhook for contact {contact_id}: {e}")

@app.get("/workspace/{filepath:path}")
async def get_file(filepath: str):
    """
    Serve a file from the workspace root while enforcing path confinement.
    
    Parameters:
    	filepath (str): Relative path (within the configured workspace root) to the requested file.
    
    Returns:
    	FileResponse: A response object that streams the requested file.
    
    Raises:
    	HTTPException: If the resolved path is outside the workspace root (403) or the file does not exist (404).
    """
    requested_path = (WORKSPACE_ROOT / filepath).resolve()

    if not requested_path.is_relative_to(WORKSPACE_ROOT):
        raise HTTPException(status_code=403, detail="Access denied")

    if not requested_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(requested_path)