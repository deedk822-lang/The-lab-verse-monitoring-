import os
import requests
from datetime import datetime, timezone
from typing import List, Dict

from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest, Filter, FilterGroup
from hubspot.crm.objects.notes import SimplePublicObjectInputForCreate
from hubspot.crm.contacts import SimplePublicObjectInput

# ========================
# CONFIG
# ========================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
PROXYCURL_KEY = os.getenv("PROXYCURL_KEY")  # Required for LinkedIn

if not all([GITHUB_TOKEN, HUBSPOT_TOKEN, PROXYCURL_KEY]):
    raise EnvironmentError("All tokens required: GITHUB_TOKEN, HUBSPOT_TOKEN, PROXYCURL_KEY")

client = HubSpot(access_token=HUBSPOT_TOKEN)

# ========================
# AUDITS
# ========================
def audit_github(handle: str) -> Dict:
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    user_resp = requests.get(f"https://api.github.com/users/{handle}", headers=headers)
    if user_resp.status_code != 200:
        return {"status": "NO_GITHUB", "evidence": "GitHub: User not found", "link": "#"}
    user = user_resp.json()

    events_resp = requests.get(f"https://api.github.com/users/{handle}/events/public", headers=headers)
    events = events_resp.json() if events_resp.status_code == 200 else []

    commits = sum(len(e.get("payload", {}).get("commits", [])) for e in events
                  if e.get("type") == "PushEvent" and e.get("created_at", "").startswith(("2025", "2024")))

    if commits >= 20: status, strength = "VERIFIED_BUILDER", f"Strong ({commits} commits)"
    elif commits >= 5: status, strength = "NUANCED_POTENTIAL", f"Moderate ({commits} commits)"
    else: status, strength = "GHOST_DEVELOPER", f"Low/none ({commits} commits)"

    return {"status": status, "evidence": f"GitHub: {strength} • {user.get('public_repos',0)} repos", "link": user.get('html_url')}

def audit_linkedin(url: str) -> Dict:
    resp = requests.get("https://nubela.co/proxycurl/api/v2/linkedin",
                        params={"url": url}, headers={"Authorization": f"Bearer {PROXYCURL_KEY}"})
    if resp.status_code != 200: return {"status": "NO_DATA", "evidence": "LinkedIn: No data", "link": url}

    data = resp.json()
    experiences = len(data.get("experiences", []))
    skills = [s.get("name", "").lower() for s in data.get("skills", [])]
    tech_match = any(k in " ".join(skills) for k in ["python", "react", "javascript", "java", "node"])

    if experiences >= 4 and tech_match: status, strength = "VERIFIED_EXPERT", "Strong experience + tech skills"
    elif experiences >= 2: status, strength = "NUANCED_PROFILE", f"{experiences} roles listed"
    else: status, strength = "WEAK_PROFILE", "Sparse public data"

    return {"status": status, "evidence": f"LinkedIn: {strength}", "link": url}

# ========================
# COMBINED CARD + DUPLICATE CHECK
# ========================
def build_card(gh: Dict, li: Dict, name: str, login: str) -> str:
    overall = "VERIFIED_BUILDER" if "VERIFIED" in gh["status"] or "VERIFIED" in li["status"] else \
              "GHOST_DEVELOPER" if "GHOST" in gh["status"] and "WEAK" in li["status"] else "NUANCED_POTENTIAL"

    icon = {"VERIFIED_BUILDER": "🟢", "NUANCED_POTENTIAL": "⚠️", "GHOST_DEVELOPER": "🔴"}[overall]

    return (
        f"**{icon} {overall}** — {name or login}\n\n"
        f"**💻 {gh['evidence']}**\n"
        f"**📋 {li['evidence']}**\n"
        "----------------------------------\n"
        f"**👮 Recommendation:** {'Fast-track interview' if overall == 'VERIFIED_BUILDER' else 'Request code sample/pass'}\n"
        "----------------------------------\n"
        f"**🔗 Sources:**\n- [GitHub]({gh['link']})\n- [LinkedIn]({li['link']})\n\n"
        f"_AI Talent Scout • {datetime.now().strftime('%H:%M on %d %B %Y')}_"
    )

def has_existing_scout_note(contact_id: str) -> bool:
    try:
        # This is a simplified check. HubSpot API for searching notes associated with a contact is complex.
        # We'll check for any note containing the scout's signature.
        notes_api = client.crm.objects.notes
        associated_notes = notes_api.get_all(object_type="contact", object_id=contact_id)
        for note in associated_notes:
            if "AI Talent Scout" in note.properties.get("hs_note_body", ""):
                return True
        return False
    except Exception as e:
        print(f"  - Could not check for existing notes: {e}")
        return False # Fail safe: proceed with posting

# ========================
# HUBSPOT LOOP
# ========================
def fetch_pending() -> List[Dict]:
    search = PublicObjectSearchRequest(
        filter_groups=[FilterGroup(filters=[
            Filter(property_name="audit_status", operator="EQ", value="Pending"),
            Filter(property_name="github_handle", operator="HAS_PROPERTY")
        ])],
        properties=["email", "github_handle", "linkedin_url", "firstname", "lastname"],
        limit=50
    )
    results = client.crm.contacts.search_api.do_search(public_object_search_request=search).results
    return [{
        "id": c.id,
        "handle": c.properties["github_handle"].strip("/").split("/")[-1],
        "li_url": c.properties.get("linkedin_url", ""),
        "name": f"{c.properties.get('firstname','')} {c.properties.get('lastname','')} ".strip()
    } for c in results if c.properties.get("github_handle")]

def post_card_and_update(contact_id: str, card: str) -> None:
    if has_existing_scout_note(contact_id):
        print("  - Duplicate prevented — scout note already exists.")
        # Still update status to prevent re-auditing
        client.crm.contacts.basic_api.update(contact_id=contact_id, simple_public_object_input=SimplePublicObjectInput(properties={"audit_status": "Audited"}))
        return

    note = SimplePublicObjectInputForCreate(
        properties={"hs_timestamp": datetime.now(timezone.utc).isoformat(), "hs_note_body": card},
        associations=[{"to": {"id": contact_id}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]}]
    )
    client.crm.objects.notes.basic_api.create(simple_public_object_input_for_create=note)
    client.crm.contacts.basic_api.update(contact_id=contact_id, simple_public_object_input=SimplePublicObjectInput(properties={"audit_status": "Audited"}))
    print("  - Audit posted & status updated to Audited.")

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    print("AI Talent Scout v7 — GitHub + LinkedIn Zero-Touch\n")
    candidates = fetch_pending()

    if not candidates:
        print("No pending candidates found.")
        exit(0)

    print(f"Found {len(candidates)} candidate(s) to audit...")
    for c in candidates:
        print(f"\nAuditing {c['name'] or '@'+c['handle']} (Contact ID: {c['id']})")

        gh = audit_github(c["handle"])
        li = audit_linkedin(c["li_url"]) if c["li_url"] else {"status": "NO_LINKEDIN", "evidence": "LinkedIn: No URL provided", "link": "#"}

        login = c["handle"]
        card = build_card(gh, li, c["name"], login)

        print(f"  - Verdict: {gh['status']} (GH) | {li['status']} (LI)")
        post_card_and_update(c["id"], card)

    print("\nRun Complete.")
