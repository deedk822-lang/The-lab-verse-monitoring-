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
    from rainmaker_orchestrator import RainmakerOrchestrator
    print(f"✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    print(f"❌ Import error in server: {e}")
    print(f"CWD: {os.getcwd()}")
    raise

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    """
    Manage application lifespan: initialize runtime resources on startup and clean them up on shutdown.
    
    On startup, attaches a RainmakerOrchestrator instance to `app.state.orchestrator` and an `httpx.AsyncClient` to `app.state.http_client`. On shutdown, closes the async HTTP client stored at `app.state.http_client`.
    """
    print("🚀 Starting up the server...")
    app.state.orchestrator = RainmakerOrchestrator()
    app.state.http_client = httpx.AsyncClient()
    print("✅ Server startup complete.")
    yield
    # Shutdown logic
    print("🔌 Shutting down the server...")
    await app.state.http_client.aclose()
    print("✅ Server shutdown complete.")

app = FastAPI(title="Lab Verse API", lifespan=lifespan)

# --- Middleware ---
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Collect Prometheus metrics for an incoming HTTP request and forward the request to the next handler.
    
    Increments the global request counter and measures the request duration while awaiting the downstream handler.
    
    Parameters:
        request (Request): The incoming FastAPI request.
        call_next (Callable[[Request], Response]): Callable that processes the request and returns a Response.
    
    Returns:
        Response: The response returned by the downstream handler.
    """
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response

# --- Exception Handlers ---
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Translate a ValueError into an HTTP 400 JSON response containing the error message.
    
    Parameters:
        exc (ValueError): The exception whose message will be returned in the response's `detail` field.
    
    Returns:
        JSONResponse: Response with status code 400 and content `{"detail": "<error message>"}`.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# --- Endpoints ---
@app.get("/health")
async def health_check():
    """
    Report a basic service health status.
    
    Returns:
        dict: Mapping containing the key "status" with the value "healthy".
    """
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """
    Serve Prometheus metrics in the Prometheus exposition (text) format.
    
    Returns:
        Response: An HTTP response with the current Prometheus metrics as plaintext in the Prometheus exposition format.
    """
    return Response(generate_latest(), media_type="text/plain")

async def get_market_intel(company_name: str, client: httpx.AsyncClient):
    """
    Return sample market intelligence for a given company.
    
    This placeholder simulates an async fetch and returns static example intelligence useful for testing and development.
    
    Parameters:
        company_name (str): Name of the company to query.
        client (httpx.AsyncClient): Asynchronous HTTP client that would be used for real external requests.
    
    Returns:
        dict: A mapping with the following keys:
            - latest_headline: A representative news headline string.
            - financial_health_signal: A short label describing financial health.
            - key_pain_point: A concise description of primary operational or financial challenges.
            - sales_hook: Suggested immediate sales/engagement messaging tailored to the company's situation.
    """
    print(f"Fetching market intel for (placeholder): {company_name}")
    # In a real scenario, this would be an async call to an external API
    # For now, we simulate an async operation
    await asyncio.sleep(0.1)
    return {
      "latest_headline": "ArcelorMittal South Africa ceases production at Newcastle steel mill and exhausts IDC rescue facility, with exclusive sale talks to IDC ending without agreement (November 2025)",
      "financial_health_signal": "Severely Negative",
      "key_pain_point": "Permanent cessation of long steel production at Newcastle and related facilities, depletion of R1.683 billion IDC lifeline, failed exclusive negotiations for potential sale/restructuring, ongoing heavy losses, and heightened supply chain vulnerabilities amid structural challenges like high energy/logistics costs and import competition",
      "sales_hook": "Avoid capital-heavy proposals. Focus on immediate crisis response services: short-term liquidity optimization, working capital advisory, retrenchment/restructuring consulting, employee transition support, and strategic advisory for asset divestment or operational wind-down to mitigate fallout from the Newcastle closure and broader long-steel shutdown"
    }

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks):
    """
    Queue a HubSpot webhook payload for background processing.
    
    Parameters:
        payload (HubSpotWebhookPayload): Incoming webhook payload containing the contact ID and message body.
    
    Returns:
        dict: A mapping with "status" set to "queued" indicating the payload was accepted for background processing.
    """
    background_tasks.add_task(process_hubspot_webhook, payload)
    return {"status": "queued"}

async def process_hubspot_webhook(payload: HubSpotWebhookPayload):
    """
    Process a HubSpot webhook payload by analyzing the lead with an AI model, updating the corresponding contact in HubSpot, and creating/enriching a deal when the AI indicates strong buying intent.
    
    The function:
    - Extracts the contact ID and message text from `payload`.
    - Sends the message to an AI analysis and expects JSON with keys `company_name`, `summary`, `intent_score` (0–10), and `suggested_action`.
    - Updates the HubSpot contact's properties `ai_lead_summary`, `ai_buying_intent`, and `ai_suggested_action` with the analysis results.
    - If `intent_score` exceeds the configured deal creation threshold, fetches market intelligence for the identified company, creates a new enriched deal with that intel, and associates the deal with the contact.
    - Logs errors encountered during processing without propagating them.
    
    Parameters:
        payload (HubSpotWebhookPayload): Webhook payload containing `objectId` (contact id) and `message_body` (lead message).
    """
    contact_id = payload.objectId
    chat_text = payload.message_body

    print(f"Processing HubSpot webhook for contact: {contact_id}")

    try:
        prompt = f"Analyze this lead: {chat_text}. Identify the lead's company. Return ONLY JSON with keys: company_name, summary, intent_score (0-10), suggested_action."
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await app.state.orchestrator._call_ollama(ollama_task, {})

        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        print(f"AI Analysis successful: {parsed_ai}")

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
        print(f"Successfully updated contact {contact_id} with AI analysis.")

        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            print(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            intel = await get_market_intel(company_name, app.state.http_client)

            deal_properties = {
                "dealname": f"{company_name} - WhatsApp Lead",
                "pipeline": "default",
                "dealstage": "appointmentscheduled",
                "news_latest_headline": intel.get('latest_headline'),
                "news_sales_hook": intel.get('sales_hook'),
                "description": f"**AI WAR ROOM BRIEF:**\n\nMARKET INTEL: {intel.get('key_pain_point')}\n\nSUGGESTED APPROACH: {intel.get('sales_hook')}"
            }
            deal_input = SimplePublicObjectInput(properties=deal_properties)
            created_deal = client.crm.deals.basic_api.create(simple_public_object_input=deal_input)

            client.crm.deals.associations_api.create(
                deal_id=created_deal.id,
                to_object_type='contact',
                to_object_id=contact_id,
                association_type='deal_to_contact'
            )
            print(f"Successfully created and associated enriched deal {created_deal.id} for contact {contact_id}.")

    except Exception as e:
        logging.error(f"Error processing HubSpot webhook for contact {contact_id}: {e}")


@app.get("/workspace/{filepath:path}")
async def get_file(filepath: str):
    """
    Serve a file from the workspace root if it exists and is within the workspace.
    
    Parameters:
        filepath (str): Path relative to the workspace root to retrieve.
    
    Returns:
        FileResponse: Response streaming the requested file.
    
    Raises:
        HTTPException: 403 if the resolved path is outside the workspace; 404 if the file does not exist.
    """
    requested_path = (WORKSPACE_ROOT / filepath).resolve()

    if not requested_path.is_relative_to(WORKSPACE_ROOT):
        raise HTTPException(status_code=403, detail="Access denied")

    if not requested_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(requested_path)