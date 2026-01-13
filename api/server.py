import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput

# The src-layout and editable install make this a standard import.
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

# --- Configuration ---
DEAL_CREATION_INTENT_SCORE_THRESHOLD = 8
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Pydantic Models ---
class ExecuteTaskPayload(BaseModel):
    type: str
    context: str
    model: Optional[str] = None
    output_filename: Optional[str] = None

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str
    subscriptionType: Optional[str] = None

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan by initializing a RainmakerOrchestrator on startup and closing it on shutdown."""
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    yield
    await orchestrator.aclose()

app = FastAPI(title="Lab Verse API", lifespan=lifespan)

# --- Endpoints ---

@app.get("/health")
async def health_check(request: Request):
    """Return the service health status."""
    try:
        orchestrator_health = await request.app.state.orchestrator.health_check()
        overall_status = "healthy" if orchestrator_health.get("status") == "healthy" else "degraded"
        return {
            "status": overall_status,
            "dependencies": {
                "orchestrator": orchestrator_health
            }
        }
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/execute")
async def execute_task(payload: ExecuteTaskPayload, request: Request):
    """Execute a task using the Rainmaker Orchestrator."""
    result = await request.app.state.orchestrator.execute_task(payload.model_dump())
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("message", "Task execution failed"))
    return result

@app.get("/intel/market")
async def get_market_intel_endpoint(company_name: str):
    """Return market intelligence for the given company name."""
    data = get_market_intel(company_name)
    return JSONResponse(content=data)

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(request: Request, payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks):
    """Enqueue processing of a HubSpot webhook payload to run in the background."""
    background_tasks.add_task(process_webhook_data, payload, request.app)
    return {"status": "accepted", "contact_id": payload.objectId}

# --- Internal Logic ---

def get_market_intel(company: str):
    """Return a simulated market intelligence report for the specified company."""
    logging.info(f"Fetching market intel for (placeholder): {company}")
    return {
        "source": "Live Search (Simulated)",
        "company": company,
        "status": "Integration Pending - Configure Perplexity/Google API",
        "timestamp": time.time()
    }

async def process_webhook_data(payload: HubSpotWebhookPayload, app: FastAPI):
    """Analyze webhook message, update contact, and conditionally create an enriched deal."""
    contact_id = payload.objectId
    chat_text = payload.message_body
    orchestrator = app.state.orchestrator

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

        # Logic: If Score > threshold, Create and Enrich Deal Automatically
        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            intel_data = get_market_intel(company_name)
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
            logging.info(f"Successfully created enriched deal {created_deal.id} for contact {contact_id}.")

    except Exception as e:
        logging.error(f"Error updating HubSpot or creating deal: {e}")
