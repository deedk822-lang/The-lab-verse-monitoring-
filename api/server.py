from fastapi import FastAPI, HTTPException
import sys
import os
import json
import logging
import time
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput
from pydantic import BaseModel
from typing import Optional

# --- Configuration ---
DEAL_CREATION_INTENT_SCORE_THRESHOLD = 8
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the root directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from rainmaker_orchestrator import RainmakerOrchestrator
    print(f"✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    print(f"❌ Import error in server: {e}. Using a dummy class for tests.")
    # This allows tests to import the module and mock the orchestrator
    class RainmakerOrchestrator:
        def __init__(self):
            self.config = {}
        async def _call_ollama(self, *args, **kwargs):
            return {}

app = FastAPI(title="Lab Verse API")
orchestrator = RainmakerOrchestrator()

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str
    subscriptionType: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/intel/market")
async def get_market_intel(company: str):
    """
    Retrieves market intelligence for a given company.
    FIX: This is now a placeholder and returns a structural response.
    """
    try:
        return {
            "source": "Live Search (Simulated)",
            "company": company,
            "status": "Integration Pending - Configure Perplexity/Google API",
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(payload: HubSpotWebhookPayload):
    contact_id = payload.objectId
    chat_text = payload.message_body

    print(f"Processing HubSpot webhook for contact: {contact_id}")

    # 1. "Zread" and Process with Ollama
    try:
        prompt = f"Analyze this lead: {chat_text}. Identify the lead's company. Return ONLY JSON with keys: company_name, summary, intent_score (0-10), suggested_action."
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await orchestrator._call_ollama(ollama_task, {})

        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        print(f"AI Analysis successful: {parsed_ai}")

    except Exception as e:
        print(f"Error calling Ollama or parsing response: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze lead with AI.")

    # 2. Update HubSpot Contact
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
        print(f"Successfully updated contact {contact_id} with AI analysis.")

    except Exception as e:
        print(f"Error updating HubSpot contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to update HubSpot contact.")

    # 3. Logic: If Score > Threshold, Create and Enrich Deal Automatically
    try:
        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            print(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            # Get market intelligence status
            intel_data = await get_market_intel(company_name)
            intel_status = intel_data.get('status', 'Market intel pending.')

            # Create the deal with enriched properties
            deal_properties = {
                "dealname": f"{company_name} - WhatsApp Lead",
                "pipeline": "default",
                "dealstage": "appointmentscheduled",
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
            print(f"Successfully created and associated enriched deal {created_deal.id} for contact {contact_id}.")

    except Exception as e:
        print(f"Error creating HubSpot deal: {e}")
        return {"status": "processed_with_deal_creation_error", "contact_id": contact_id}

    return {"status": "processed", "contact_id": contact_id}
