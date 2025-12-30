from fastapi import FastAPI
import sys
import os
 feat/hubspot-ollama-integration-9809589759324023108

import json
import hashlib
import hmac
import base64
import logging
import httpx
import requests
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput
from hubspot.core.exceptions import ApiException
from pydantic import BaseModel
from typing import Optional
 main

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
 feat/hubspot-ollama-integration-9809589759324023108


def get_market_intel(company_name: str):
    """
    Hits the live internet to find news from the last 30-90 days only.
    Strictly filters for 'Business Risk' and 'Sales Triggers'.
    """
    perplexity_api_key = orchestrator.config.get("PERPLEXITY_API_KEY")
    if not perplexity_api_key:
        logging.error("PERPLEXITY_API_KEY is not set.")
        return {
            "status": "UNKNOWN",
            "headline": "Search failed: API key not configured",
            "risk_factor": "Manual check required",
            "sales_hook": "Ask lead about current projects."
        }

    url = "https://api.perplexity.ai/chat/completions"
    system_instruction = (
        "You are a Corporate Intelligence Officer in South Africa. "
        "Your goal is to protect the sales team from wasting time on dead leads "
        "and find the 'Golden Hook' for good leads."
    )
    user_query = (
        f"Search for the absolute latest news (Oct 2025 - Dec 2025) for '{company_name}' in South Africa. "
        "Prioritize sources like: Mining Weekly, News24, Engineering News, Reuters. "
        "\n\n"
        "Identify strictly:\n"
        "1. FINANCIAL HEALTH (Is there a liquidity crisis? Share price crash?)\n"
        "2. OPERATIONAL STATE (Retrenchments? Strikes? Wind-down? New Projects?)\n"
        "3. THE SALES HOOK (Based on this news, what exact angle should a salesman use?)\n"
        "\n"
        "Return the answer in this JSON format only:\n"
        '{ "status": "CRITICAL/CAUTION/GROWTH", "headline": "...", "risk_factor": "...", "sales_hook": "..." }'
    )

    payload = {
        "model": "llama-3.1-sonar-large-128k-online",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }

    try:
        logging.info(f"🕵️  Scouting {company_name} for real-time intel...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        content = response.json()['choices'][0]['message']['content']

        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")

        return json.loads(content)

    except requests.exceptions.RequestException as e:
        logging.error(f"Perplexity API request failed: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON from Perplexity response: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_market_intel: {e}")

    return {
        "status": "UNKNOWN",
        "headline": "Search failed",
        "risk_factor": "Manual check required",
        "sales_hook": "Ask lead about current projects."
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
                "news_latest_headline": intel.get('headline'),
                "news_sales_hook": intel.get('sales_hook'),
                "description": f"**AI WAR ROOM BRIEF:**\n\nMARKET INTEL: {intel.get('risk_factor')}\n\nSUGGESTED APPROACH: {intel.get('sales_hook')}"
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
 main
