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
from typing import Optional

# --- Prometheus Metrics ---
request_count = Counter('http_requests_total', 'Total requests')
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

# --- Pydantic Models ---
class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str
    subscriptionType: Optional[str] = None

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
    logging.info("✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    logging.exception(f"❌ Import error in server: {e}. CWD: {os.getcwd()}")
    raise

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logging.info("🚀 Starting up the server...")
    app.state.orchestrator = RainmakerOrchestrator()
    app.state.http_client = httpx.AsyncClient()
    logging.info("✅ Server startup complete.")
    yield
    # Shutdown logic
    logging.info("🔌 Shutting down the server...")
    await app.state.http_client.aclose()
    await app.state.orchestrator.aclose()
    logging.info("✅ Server shutdown complete.")

app = FastAPI(title="Lab Verse API", lifespan=lifespan)

# --- Middleware ---
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response

# --- Exception Handlers ---
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# --- Endpoints ---
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

async def get_market_intel(company_name: str, client: httpx.AsyncClient):
    """
    Retrieves market intelligence for a given company.
    This is a placeholder and returns static data.
    """
    logging.info(f"Fetching market intel for (placeholder): {company_name}")
    await asyncio.sleep(0.1) # Simulate async operation
    return {
      "latest_headline": "ArcelorMittal South Africa ceases production at Newcastle steel mill and exhausts IDC rescue facility, with exclusive sale talks to IDC ending without agreement (November 2025)",
      "financial_health_signal": "Severely Negative",
      "key_pain_point": "Permanent cessation of long steel production at Newcastle and related facilities, depletion of R1.683 billion IDC lifeline, failed exclusive negotiations for potential sale/restructuring, ongoing heavy losses, and heightened supply chain vulnerabilities amid structural challenges like high energy/logistics costs and import competition",
      "sales_hook": "Avoid capital-heavy proposals. Focus on immediate crisis response services: short-term liquidity optimization, working capital advisory, retrenchment/restructuring consulting, employee transition support, and strategic advisory for asset divestment or operational wind-down to mitigate fallout from the Newcastle closure and broader long-steel shutdown"
    }

async def process_hubspot_webhook(payload: HubSpotWebhookPayload, app: FastAPI):
    contact_id = payload.objectId
    chat_text = payload.message_body
    orchestrator = app.state.orchestrator
    http_client = app.state.http_client

    logging.info(f"Processing HubSpot webhook for contact: {contact_id}")

    try:
        prompt = f"Analyze this lead: {chat_text}. Identify the lead's company. Return ONLY JSON with keys: company_name, summary, intent_score (0-10), suggested_action."
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await orchestrator._call_ollama(ollama_task, {})
        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        logging.info(f"AI Analysis successful: {parsed_ai}")
    except Exception:
        logging.exception("Error calling Ollama or parsing response")
        return

    try:
        hubspot_access_token = orchestrator.config.get('HUBSPOT_ACCESS_TOKEN')
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
    except Exception:
        logging.exception(f"Error updating HubSpot contact {contact_id}")
        return

    try:
        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            logging.info(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            intel = await get_market_intel(company_name, http_client)
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
            logging.info(f"Successfully created and associated enriched deal {created_deal.id} for contact {contact_id}.")
    except Exception as e:
        logging.error(f"Error creating HubSpot deal for contact {contact_id}", exc_info=e)

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(request: Request, payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_hubspot_webhook, payload, request.app)
    return {"status": "accepted", "contact_id": payload.objectId}

@app.get("/workspace/{filepath:path}")
async def get_file(filepath: str):
    requested_path = (WORKSPACE_ROOT / filepath).resolve()

    if not requested_path.is_relative_to(WORKSPACE_ROOT):
        raise HTTPException(status_code=403, detail="Access denied")

    if not requested_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(requested_path)
