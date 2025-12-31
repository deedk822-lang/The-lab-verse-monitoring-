import os
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest, Filter, FilterGroup
from hubspot.crm.objects.notes import SimplePublicObjectInputForCreate
from hubspot.crm.contacts import SimplePublicObjectInput
from hubspot.crm.objects import BatchReadInputSimplePublicObjectId

# ========================
# CONFIG (Using the specific name provided)
# ========================
KIMI_GITHUB_KEY = os.getenv("KIMI_GITHUB_KEY")
HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

# Removed PROXYCURL_KEY check as Proxycurl is defunct
if not all([KIMI_GITHUB_KEY, HUBSPOT_TOKEN]):
    raise EnvironmentError("Required: KIMI_GITHUB_KEY, HUBSPOT_TOKEN")

client = HubSpot(access_token=HUBSPOT_TOKEN)

# ========================
# AUDITS (GitHub Only - Proxycurl Defunct)
# ========================
def audit_github(handle: str) -> Dict[str, str]:
    headers = {
        "Authorization": f"token {KIMI_GITHUB_KEY}",
        "Accept": "application/vnd.github.v3+json", # Using v3 for consistency
    }
    try:
        # FIX: Corrected URL (removed space)
        user_resp = requests.get(
            f"https://api.github.com/users/{handle}", headers=headers, timeout=10
        )
        if user_resp.status_code == 404:
            return {
                "status": "NO_GITHUB",
                "evidence": "GitHub: User not found",
                "link": "#",
            }
        user_resp.raise_for_status() # Raise exception for other non-200 codes
        user = user_resp.json()

        # FIX: Corrected URL (removed space)
        events_resp = requests.get(
            f"https://api.github.com/users/{handle}/events/public",
            headers=headers,
            timeout=10,
        )
        events_resp.raise_for_status()
        events = events_resp.json()

        # Improved activity calculation with multiple signals
        cutoff_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        activity_score = 0
        repos_contributed_to = set()

        for e in events:
            try:
                event_time = datetime.fromisoformat(e['created_at'].replace('Z', '+00:00'))
            except (ValueError, KeyError):
                continue # Skip if date parsing fails

            if event_time >= cutoff_date:
                repos_contributed_to.add(e.get('repo', {}).get('name', 'unknown_repo'))

                if e.get("type") == "PushEvent":
                    activity_score += len(e.get("payload", {}).get("commits", []))
                elif e.get("type") == "PullRequestEvent" and e.get("payload", {}).get("action") == "opened":
                    activity_score += 1.5
                elif e.get("type") == "PullRequestReviewEvent":
                    activity_score += 1
                elif e.get("type") == "IssuesEvent" and e.get("payload", {}).get("action") == "opened":
                    activity_score += 0.5

        # Determine status based on score and other signals
        if activity_score >= 15:
            status, strength = "VERIFIED_BUILDER", f"High activity (Score: {activity_score:.1f})"
        elif activity_score >= 5:
            status, strength = "VERIFIED_BUILDER", f"Solid activity (Score: {activity_score:.1f})"
        elif activity_score > 0:
            status, strength = "NUANCED_POTENTIAL", f"Light activity (Score: {activity_score:.1f})"
        else:
            # Check for MemberEvent as proxy for private activity
            member_events = []
            for e in events:
                if e.get("type") == "MemberEvent":
                    try:
                        event_time = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
                        if event_time >= cutoff_date:
                            member_events.append(e)
                    except (ValueError, KeyError):
                        continue
            if member_events:
                status, strength = "NUANCED_POTENTIAL", f"Signs of private/org activity ({len(member_events)} MemberEvents)"
            else:
                status, strength = "GHOST_DEVELOPER", "No significant public activity in 2024-2025"

        return {
            "status": status,
            "evidence": f"GitHub: {strength} | Repos: {user.get('public_repos', 0)} | Score: {activity_score:.1f}",
            "link": user.get("html_url", "#"),
        }
    except requests.RequestException as e:
        print(f"GitHub audit failed for {handle}: {e}") # Log error
        return {
            "status": "ERROR",
            "evidence": f"GitHub: Request failed ({e})",
            "link": "#",
        }

# ========================
# CARD BUILDER (GitHub Only)
# ========================
def build_card(gh: Dict[str, str], name: str, login: str) -> str:
    overall = gh["status"]
    icon_map = {"VERIFIED_BUILDER": "🟢", "NUANCED_POTENTIAL": "⚠️", "GHOST_DEVELOPER": "🔴", "ERROR": "❌", "NO_GITHUB": "❓"}
    icon = icon_map.get(overall, "❓")

    return (
        f"**{icon} {overall}** — {name or '@' + login}\n\n"
        f"**💻 {gh['evidence']}**\n"
        "----------------------------------\n"
        f"**👮 Recommendation:** {'Fast-track to technical interview' if 'VERIFIED' in overall else 'Request code sample or pass'}\n"
        "----------------------------------\n"
        f"**🔗 Source:**\n- [GitHub]({gh['link']})\n\n"
        f"_AI Talent Scout • {datetime.now().strftime('%H:%M on %d %B %Y')}_"
    )

# ========================
# HUBSPOT LOOP
# ========================
def fetch_pending() -> List[Dict[str, str]]:
    search = PublicObjectSearchRequest(
        filter_groups=[FilterGroup(filters=[
            Filter(property_name="audit_status", operator="EQ", value="Pending"),
            Filter(property_name="github_handle", operator="NEQ", value=""), # Handle not empty
        ])],
        properties=["github_handle", "firstname", "lastname"], # Removed unused properties
        limit=50,
    )

    results = client.crm.contacts.search_api.do_search(
        public_object_search_request=search
    ).results

    contacts = []
    for c in results:
        handle = c.properties.get("github_handle")
        if handle and handle.strip():
            contacts.append({
                "id": c.id,
                "handle": handle.strip("/").split("/")[-1],
                "name": f"{c.properties.get('firstname', '')} {c.properties.get('lastname', '')}".strip(),
            })
    return contacts

def has_existing_scout_note(contact_id: str) -> bool:
    try:
        # Get all note associations for the contact
        associated_notes_response = client.crm.associations.v4.basic_api.get_page(
            from_object_type="contacts",
            to_object_type="notes",
            from_object_id=contact_id,
        )
        note_ids = [assoc.to_object_id for assoc in associated_notes_response.results]

        if not note_ids:
            return False

        # Batch read the notes to check their content
        notes_batch_input = BatchReadInputSimplePublicObjectId(
            inputs=[{"id": note_id} for note_id in note_ids],
            properties=["hs_note_body"]
        )
        notes_response = client.crm.objects.notes.batch_api.read(
            batch_read_input_simple_public_object_id=notes_batch_input
        )

        for note in notes_response.results:
            if "AI Talent Scout" in note.properties.get("hs_note_body", ""):
                return True
        return False
    except Exception as e:
        print(f"  - Could not check for existing notes: {e}")
        return False # Fail safe: proceed with posting

def post_card_and_update(contact_id: str, card: str) -> None:
    if has_existing_scout_note(contact_id):
        print("   → Duplicate prevented — scout note already exists.")
        # Still update status to prevent re-auditing
        client.crm.contacts.basic_api.update(
            contact_id=contact_id,
            simple_public_object_input=SimplePublicObjectInput(
                properties={"audit_status": "Audited"}
            ),
        )
        return

    note = SimplePublicObjectInputForCreate(
        properties={
            "hs_timestamp": datetime.now(timezone.utc).isoformat(),
            "hs_note_body": card,
        },
        associations=[{
            "to": {"id": contact_id},
            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
        }],
    )
    client.crm.objects.notes.basic_api.create(
        simple_public_object_input_for_create=note
    )
    client.crm.contacts.basic_api.update(
        contact_id=contact_id,
        simple_public_object_input=SimplePublicObjectInput(
            properties={"audit_status": "Audited"}
        ),
    )
    print("   → Audit posted & status updated to Audited")

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    print("AI Talent Scout v8 Enhanced (GitHub Only) — Proxycurl Removed, Lint/Security Fixed\n")

    candidates = fetch_pending()

    if not candidates:
        print("No pending candidates found.")
        exit(0)

    print(f"Found {len(candidates)} candidate(s) to audit...\n")

    for c in candidates:
        print(f"Auditing {c['name'] or '@' + c['handle']} (Contact ID: {c['id']})")

        gh = audit_github(c["handle"])

        card = build_card(gh, c["name"], c["handle"])

        print(f"   Verdict: {gh['status']}\n")

        post_card_and_update(c["id"], card)

        print("-" * 60)

    print("\nRun complete.")
