from fastapi import FastAPI
import sys
import os
import json
import logging
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
    print(f"❌ Import error in server: {e}")
    print(f"CWD: {os.getcwd()}")
    raise

app = FastAPI(title="Lab Verse API")
orchestrator = RainmakerOrchestrator()

class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# TODO: Replace this with a real market intelligence API (e.g., Perplexity, Google Search)
def get_market_intel(company_name: str):
    """
    Retrieves market intelligence for a given company.
    This is a placeholder and returns static data.
    """
    print(f"Fetching market intel for (placeholder): {company_name}")
    return {
      "latest_headline": "ArcelorMittal South Africa ceases production at Newcastle steel mill and exhausts IDC rescue facility, with exclusive sale talks to IDC ending without agreement (November 2025)",
      "financial_health_signal": "Severely Negative",
      "key_pain_point": "Permanent cessation of long steel production at Newcastle and related facilities, depletion of R1.683 billion IDC lifeline, failed exclusive negotiations for potential sale/restructuring, ongoing heavy losses, and heightened supply chain vulnerabilities amid structural challenges like high energy/logistics costs and import competition",
      "sales_hook": "Avoid capital-heavy proposals. Focus on immediate crisis response services: short-term liquidity optimization, working capital advisory, retrenchment/restructuring consulting, employee transition support, and strategic advisory for asset divestment or operational wind-down to mitigate fallout from the Newcastle closure and broader long-steel shutdown"
    }

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

        # The response from _call_ollama is a dict with the content being a stringified JSON
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

    # 3. Logic: If Score > 8, Create and Enrich Deal Automatically
    try:
        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > 8:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            print(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            # Get market intelligence
            intel = get_market_intel(company_name)

            # Create the deal with enriched properties
            deal_properties = {
                "dealname": f"{company_name} - WhatsApp Lead",
                "pipeline": "default",
                "dealstage": "appointmentscheduled", # Example stage
                "news_latest_headline": intel.get('latest_headline'),
                "news_sales_hook": intel.get('sales_hook'),
                "description": f"**AI WAR ROOM BRIEF:**\n\nMARKET INTEL: {intel.get('key_pain_point')}\n\nSUGGESTED APPROACH: {intel.get('sales_hook')}"
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
        # Don't raise an exception here, as the contact update was successful.
        # Log the error and return a success response.
        return {"status": "processed_with_deal_creation_error", "contact_id": contact_id}

    return {"status": "processed", "contact_id": contact_id}
