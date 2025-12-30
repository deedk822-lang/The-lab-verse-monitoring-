from fastapi import FastAPI, Request, HTTPException
import sys
import os
import json
import hashlib
import hmac
import base64
import logging
import httpx
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput
from hubspot.core.exceptions import ApiException
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
    logging.info("✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    logging.error(f"❌ Import error in server: {e}")
    logging.error(f"CWD: {os.getcwd()}")
    raise

app = FastAPI(title="Lab Verse API")
orchestrator = RainmakerOrchestrator()

# Pydantic model for incoming HubSpot webhook data
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
    logging.info(f"Fetching market intel for (placeholder): {company_name}")
    return {
      "latest_headline": "ArcelorMittal South Africa ceases production at Newcastle steel mill and exhausts IDC rescue facility, with exclusive sale talks to IDC ending without agreement (November 2025)",
      "financial_health_signal": "Severely Negative",
      "key_pain_point": "Permanent cessation of long steel production at Newcastle and related facilities, depletion of R1.683 billion IDC lifeline, failed exclusive negotiations for potential sale/restructuring, ongoing heavy losses, and heightened supply chain vulnerabilities amid structural challenges like high energy/logistics costs and import competition",
      "sales_hook": "Avoid capital-heavy proposals. Focus on immediate crisis response services: short-term liquidity optimization, working capital advisory, retrenchment/restructuring consulting, employee transition support, and strategic advisory for asset divestment or operational wind-down to mitigate fallout from the Newcastle closure and broader long-steel shutdown"
    }

async def verify_hubspot_signature(request: Request):
    """Verifies the HubSpot webhook signature (v3)."""
    client_secret = orchestrator.config.get('HUBSPOT_CLIENT_SECRET')
    if not client_secret:
        logging.error("CRITICAL: HUBSPOT_CLIENT_SECRET is not configured. Cannot verify webhook signature.")
        raise HTTPException(status_code=500, detail="Webhook client secret is not configured on the server.")

    signature = request.headers.get('x-hubspot-signature-v3')
    timestamp = request.headers.get('x-hubspot-request-timestamp')

    if not signature or not timestamp:
        raise HTTPException(status_code=403, detail="Missing HubSpot signature headers.")

    # Recreate the source string
    source_string = request.method + request.url.path
    body = await request.body()
    source_string += body.decode('utf-8')
    source_string += timestamp

    # Compute the HMAC-SHA256 hash
    hashed = hmac.new(
        client_secret.encode('utf-8'),
        source_string.encode('utf-8'),
        hashlib.sha256
    ).digest()
    computed_signature = base64.b64encode(hashed).decode('utf-8')

    if not hmac.compare_digest(computed_signature, signature):
        raise HTTPException(status_code=403, detail="Invalid HubSpot signature.")

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(request: Request, payload: HubSpotWebhookPayload):
    # Security First: Verify the incoming request is from HubSpot
    await verify_hubspot_signature(request)

    contact_id = payload.objectId
    chat_text = payload.message_body
    logging.info(f"Processing HubSpot webhook for contact: {contact_id}")

    # --- Step 1: AI Analysis ---
    try:
        prompt = f"Analyze this lead: {chat_text}. Identify the lead's company. Return ONLY JSON with keys: company_name, summary, intent_score (0-10), suggested_action."
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await orchestrator._call_ollama(ollama_task, {})
        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        logging.info(f"AI Analysis successful: {parsed_ai}")
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logging.error(f"Error calling Ollama: {e}")
        raise HTTPException(status_code=502, detail="Failed to analyze lead with AI (Ollama connection error).")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing Ollama JSON response: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze lead with AI (Invalid JSON response).")
    except Exception as e:
        logging.error(f"An unexpected error occurred during AI analysis: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during AI analysis.")


    # --- Step 2: Update HubSpot Contact ---
    # Initialize HubSpot client outside of the try block
    hubspot_access_token = orchestrator.config.get('HUBSPOT_ACCESS_TOKEN')
    if not hubspot_access_token:
        logging.error("HUBSPOT_ACCESS_TOKEN is not set.")
        raise HTTPException(status_code=500, detail="HubSpot API token is not configured.")
    client = HubSpot(access_token=hubspot_access_token)

    try:
        properties_to_update = {
            "ai_lead_summary": parsed_ai.get('summary', 'N/A'),
            "ai_buying_intent": parsed_ai.get('intent_score', 0),
            "ai_suggested_action": parsed_ai.get('suggested_action', 'N/A')
        }
        client.crm.contacts.basic_api.update(contact_id, {"properties": properties_to_update})
        logging.info(f"Successfully updated contact {contact_id} with AI analysis.")
    except ApiException as e:
        logging.error(f"Error updating HubSpot contact {contact_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to update HubSpot contact due to API error.")
    except Exception as e:
        logging.error(f"An unexpected error occurred while updating HubSpot contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating HubSpot contact.")


    # --- Step 3: Conditional Deal Creation ---
    try:
        intent_score = parsed_ai.get('intent_score', 0)
        if intent_score > DEAL_CREATION_INTENT_SCORE_THRESHOLD:
            company_name = parsed_ai.get('company_name', 'Unknown Company')
            logging.info(f"Intent score ({intent_score}) is high for {company_name}. Creating and enriching a new deal.")

            intel = get_market_intel(company_name)
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
    except ApiException as e:
        logging.error(f"Error creating or associating HubSpot deal for contact {contact_id}: {e}")
        return {"status": "processed_with_deal_creation_error", "contact_id": contact_id}
    except Exception as e:
        logging.error(f"An unexpected error occurred during deal creation for contact {contact_id}: {e}")
        return {"status": "processed_with_deal_creation_error", "contact_id": contact_id}

    return {"status": "processed", "contact_id": contact_id}
