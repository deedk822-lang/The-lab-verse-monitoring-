from fastapi import FastAPI, HTTPException
import sys
import os
import json
import logging
import time
from hubspot.crm.deals import SimplePublicObjectInput
from pydantic import BaseModel
from typing import Optional

import os
import sys
import json
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput

# --- Pydantic Model Definition ---
class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str
    subscriptionType: Optional[str] = None

# --- Configuration ---
DEAL_CREATION_INTENT_SCORE_THRESHOLD = 8
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the root directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
    logging.info("✅ Successfully imported rainmaker_orchestrator in server")
except ImportError:
    logging.exception(f"❌ Import error in server. CWD: {os.getcwd()}")
    raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    """
    Create a RainmakerOrchestrator on startup and close it on shutdown.
    
    On startup, instantiate RainmakerOrchestrator and attach it to app.state.orchestrator. On shutdown, call its `aclose()` coroutine to release resources and perform cleanup.
    """
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    yield
    # Shutdown
    await orchestrator.aclose()

app = FastAPI(title="Lab Verse API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """
    Return the service health status.
    
    Returns:
        A mapping with the key "status" set to "healthy".
    """
    return {"status": "healthy"}

@app.get("/intel/market")
async def get_market_intel(company: str):
    """
    Return a simulated market intelligence report for the specified company.
    
    Parameters:
        company (str): The company name to retrieve market intelligence for.
    
    Returns:
        dict: A structured market intelligence object with keys:
            - source (str): The data source label (simulated).
            - company (str): Echoes the requested company name.
            - status (str): Integration/configuration status or note.
            - timestamp (float): Unix timestamp of the report generation.
    """
    logging.info(f"Fetching market intel for (placeholder): {company}")
    return {
        "source": "Live Search (Simulated)",
        "company": company,
        "status": "Integration Pending - Configure Perplexity/Google API",
        "timestamp": time.time()
    }

async def process_webhook_data(payload: HubSpotWebhookPayload, app: FastAPI):
    """
    Analyze an incoming HubSpot webhook message with the orchestrator, update the corresponding HubSpot contact with AI-derived fields, and conditionally create and associate an enriched deal.
    
    Sends payload.message_body to the orchestrator for JSON-formatted AI analysis, updates the contact identified by payload.objectId with properties `ai_lead_summary`, `ai_buying_intent`, and `ai_suggested_action`, and if the returned `intent_score` exceeds the configured threshold creates a new deal enriched with market intelligence and associates it with the contact. On errors during analysis or contact update the function logs the exception and returns early; errors during deal creation are logged and not propagated.
    
    Parameters:
        payload (HubSpotWebhookPayload): Incoming webhook payload containing `objectId` (contact id) and `message_body` (text to analyze).
        app (FastAPI): FastAPI application instance used to access app.state.orchestrator and its configuration for HubSpot credentials.
    """
    contact_id = payload.objectId
    chat_text = payload.message_body

    logging.info(f"Processing HubSpot webhook for contact: {contact_id}")

    # 1. "Zread" and Process with Ollama
    # NOTE: Using the private method `_call_ollama` as the orchestrator's public
    # `execute_task` method is designed for a different, more complex workflow.
    # A future refactor should expose a dedicated public method for this type of analysis.
    try:
        prompt = f"Analyze this lead: {chat_text}. Identify the lead's company. Return ONLY JSON with keys: company_name, summary, intent_score (0-10), suggested_action."
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await app.state.orchestrator._call_ollama(ollama_task, {})

        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        logging.info(f"AI Analysis successful: {parsed_ai}")

    except Exception:
        logging.exception("Error calling Ollama or parsing response")
        # In a real app, you might want to retry or send an alert
        return

    # 2. Update HubSpot Contact
    try:
        client = app.state.orchestrator.hubspot_client
        properties_to_update = {
            "ai_lead_summary": parsed_ai.get('summary', 'N/A'),
            "ai_buying_intent": parsed_ai.get('intent_score', 0),
            "ai_suggested_action": parsed_ai.get('suggested_action', 'N/A')
        }

        client.crm.contacts.basic_api.update(contact_id, {"properties": properties_to_update})
        logging.info(f"Successfully updated contact {contact_id} with AI analysis.")

    except Exception:
        logging.exception("Error updating HubSpot contact")
        return

    # 3. Logic: If Score > threshold, Create and Enrich Deal Automatically
    try:
        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            logging.info(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            # Get market intelligence status
            intel_data = await get_market_intel(company_name)
            intel_status = intel_data.get('status', 'Market intel pending.')

            # Create the deal with enriched properties
            deal_properties = {
                "dealname": f"{company_name} - WhatsApp Lead",
                "pipeline": "default",
                "dealstage": "appointmentscheduled", # Example stage
                "description": f"**AI WAR ROOM BRIEF:**\n\nMARKET INTEL: {intel_status}"
            }
            deal_input = SimplePublicObjectInput(properties=deal_properties)
            created_deal = client.crm.deals.basic_api.create(simple_public_object_input=deal_input)

            # Associate the new deal with the contact
            client.crm.deals.associations_api.create(
                deal_id=created_deal.id,
                to_object_type='contact',
                to_object_id=contact_id,
                association_type='deal_to_contact'
            )
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
    if not request.app.state.orchestrator.hubspot_client:
        raise HTTPException(status_code=503, detail="HubSpot client is not configured")
    background_tasks.add_task(process_webhook_data, payload, request.app)
    return {"status": "accepted", "contact_id": payload.objectId}
