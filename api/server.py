import os
import logging
 feat/implement-authority-engine
import time
from hubspot.crm.deals import SimplePublicObjectInput
from pydantic import BaseModel

from contextlib import asynccontextmanager
 main
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
import opik

# Internal Imports
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api")

class ExecuteTaskPayload(BaseModel):
    type: str
    context: str
    model: Optional[str] = None
    output_filename: Optional[str] = None

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Manage lifecycle of the Authority Engine.\"\"\"
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    logger.info("Authority Engine initialized and ready.")
    yield
    await orchestrator.aclose()
    logger.info("Authority Engine shut down.")

app = FastAPI(
    title="Rainmaker Authority API",
    description="The secure gateway for the 4-Judge Authority Engine.",
    version="1.1.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {
        "status": "connected",
        "engine": "Authority Engine v1.1",
        "features": ["4-Judge Flow", "Self-Healing", "Opik Telemetry"]
    }

 feat/implement-authority-engine
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

@app.post("/webhook/hubspot")
async def hubspot_webhook(payload: HubSpotWebhookPayload, background_tasks: BackgroundTasks, request: Request):
    \"\"\"Asynchronous entry point for HubSpot events.\"\"\"
    orchestrator = request.app.state.orchestrator
    # Use model_dump() for Pydantic v2 compatibility
    background_tasks.add_task(orchestrator.run_authority_flow, payload.model_dump())
    return {"status": "accepted", "message": "Authority Flow queued."}

@app.post("/execute")
async def execute(payload: ExecuteTaskPayload, request: Request, background_tasks: BackgroundTasks):
    """Asynchronous execution for direct agent tasks."""
    orchestrator = request.app.state.orchestrator
    # This is a long-running task. Running it in the background
    # allows us to return a response to the client immediately.
    background_tasks.add_task(orchestrator.execute_task, payload.model_dump())
    return {"status": "accepted", "message": "Task queued for execution."}
 main
