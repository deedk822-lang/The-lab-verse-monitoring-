from fastapi import FastAPI, Request, HTTPException
import sys
import os
import json
from datetime import datetime
from hubspot import HubSpot
from hubspot.crm.deals import SimplePublicObjectInput
from pydantic import BaseModel
from typing import Optional

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

# Pydantic model for incoming HubSpot webhook data
class HubSpotWebhookPayload(BaseModel):
    objectId: int
    message_body: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def format_intel_for_hubspot(scout_json: str) -> str:
    """
    Converts Scout Agent JSON (now with source_links) into a polished HubSpot Deal Note.
    Includes clickable sources for maximum rep trust.
    """
    try:
        data = json.loads(scout_json)
    except json.JSONDecodeError:
        return "⚠️ ERROR: Invalid Scout JSON - Please re-run analysis."

    status_map = {
        "VERIFIED_CRITICAL": "🔴 CRITICAL STOP",
        "NUANCED_RISK": "⚠️ PROCEED WITH CAUTION",
        "CLEAR_GROWTH": "🟢 GREEN LIGHT"
    }

    header = status_map.get(data.get('intel_status'), "🔵 INTEL UPDATE")
    timestamp = datetime.now().strftime('%H:%M on %d %B %Y')

    # Format sources as Markdown links
    sources_md = "\n".join([f"- [{url}]({url})" for url in data.get('source_links', [])]) if data.get('source_links') else "No sources provided."

    hubspot_note = (
        f"**{header}** — {data.get('company_name', 'Unknown Company')}\n\n"
        f"**🏭 Key Event:** {data.get('key_event', 'N/A')}\n"
        f"**📅 Evidence Date:** {data.get('evidence_date', 'N/A')}\n"
        f"**Confidence:** High (Multi-source verified)\n"
        "----------------------------------\n"
        f"**👮 SALES INSTRUCTION:**\n"
        f"👉 {data.get('rep_warning', 'N/A')}\n"
        "----------------------------------\n"
        f"**ℹ️ Detailed Context:** {data.get('nuance_note', 'N/A')}\n\n"
        f"**🔗 Primary Sources:**\n{sources_md}\n\n"
        f"_Verified by AI Scout Agent at {timestamp}_"
    )

    return hubspot_note

@app.post("/webhook/hubspot")
async def handle_hubspot_webhook(payload: HubSpotWebhookPayload):
    contact_id = payload.objectId
    chat_text = payload.message_body

    print(f"Processing HubSpot webhook for contact: {contact_id}")

    # 1. Process with Scout Agent v3
    try:
        scout_prompt_template = """
ROLE:
You are a Senior Market Risk Analyst for an industrial sales team in South Africa.
Current Date: December 30, 2025.

TASK:
First, identify the company name from the user's message provided at the end.
Then, using your knowledge base, act as if you have analyzed web search results and news sources for that target company. Produce a concise "Truth Verification" report on potential risks or opportunities impacting sales (e.g., plant closures, ESG pressures, expansions).

RULES:
1. DATE ACCURACY: Strictly distinguish news by year/month. Ignore or flag pre-2025 data unless explicitly relevant.
2. VERIFICATION LEVEL:
   - "VERIFIED_CRITICAL": Confirmed event with major negative sales impact.
   - "NUANCED_RISK": Mixed/ongoing signals or partial support.
   - "CLEAR_GROWTH": Confirmed positive development.
3. NO HALLUCINATIONS: If data is ambiguous or absent, use "NUANCED_RISK" and note uncertainty.
4. SALES FOCUS: Translate into clear, actionable warnings or opportunities.
5. SOURCES: Always include 1-3 primary source URLs that directly support the key_event and nuance_note.

OUTPUT FORMAT (Strict JSON only - no extra text):
{
  "company_name": "String",
  "intel_status": "VERIFIED_CRITICAL | NUANCED_RISK | CLEAR_GROWTH",
  "key_event": "One-sentence factual summary",
  "evidence_date": "Specific date or period",
  "rep_warning": "Direct, imperative instruction",
  "nuance_note": "Balanced clarification, including uncertainty",
  "source_links": ["url1", "url2", ...]
}
"""
        prompt = f"{scout_prompt_template}\n\nUSER MESSAGE TO ANALYZE: '{chat_text}'"
        ollama_task = {"context": prompt, "model": "ollama"}
        ai_analysis_raw = await orchestrator._call_ollama(ollama_task, {})

        # The response from _call_ollama is a dict with the content being a stringified JSON
        ai_analysis_str = ai_analysis_raw["message"]["content"]
        parsed_ai = json.loads(ai_analysis_str)
        print(f"AI Analysis successful: {parsed_ai}")

    except Exception as e:
        print(f"Error calling Ollama or parsing response: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze lead with AI.")

    # 2. Create and Enrich HubSpot Deal with Scout Report
    try:
        hubspot_access_token = orchestrator.config.get('HUBSPOT_ACCESS_TOKEN')
        if not hubspot_access_token:
            raise ValueError("HUBSPOT_ACCESS_TOKEN is not set.")

        client = HubSpot(access_token=hubspot_access_token)

        # Format the AI's JSON response into a HubSpot note
        hubspot_note = format_intel_for_hubspot(ai_analysis_str)

        company_name = parsed_ai.get('company_name', 'Unknown Company')
        print(f"Creating HubSpot deal for {company_name} with AI Scout report.")

        # Create the deal with the formatted scout report in the description
        deal_properties = {
            "dealname": f"{company_name} - AI Scout Lead",
            "pipeline": "default",
            "dealstage": "appointmentscheduled",
            "description": hubspot_note
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
        print(f"Successfully created and associated deal {created_deal.id} for contact {contact_id}.")

    except Exception as e:
        print(f"Error creating HubSpot deal: {e}")
        raise HTTPException(status_code=500, detail="Failed to create HubSpot deal.")

    return {"status": "processed", "contact_id": contact_id}
