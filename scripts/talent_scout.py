import os
import time  # For potential rate limit handling
from datetime import datetime, timezone
from typing import Dict, Optional

import requests
from hubspot import HubSpot
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest
from hubspot.crm.objects.notes import SimplePublicObjectInputForCreate
from hubspot.exceptions import ApiError  # Import specific exception

# ========================
# CONFIG
# ========================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("❌ GITHUB_TOKEN environment variable is missing.")
if not HUBSPOT_TOKEN:
    print("⚠️ HUBSPOT_TOKEN not found. Running in dry-run mode (prints only).")

HUBSPOT_CLIENT = HubSpot(access_token=HUBSPOT_TOKEN) if HUBSPOT_TOKEN else None

# ========================
# CORE: Enhanced GitHub Audit
# ========================
def audit_github(handle: str) -> Optional[Dict]:
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json" # Using v3 for consistency
    }

    # --- FIX 1: Corrected URL Concatenation (Removed fatal space) ---
    user_url = f"https://api.github.com/users/{handle}"
    events_url = f"https://api.github.com/users/{handle}/events/public"

    try:
        # Fetch User Profile
        user_resp = requests.get(user_url, headers=headers)
        if user_resp.status_code == 404:
            print(f"⚠️ GitHub user not found: {handle}")
            return None
        user_resp.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        user = user_resp.json()

        # Fetch Events
        events_resp = requests.get(events_url, headers=headers)

        # --- ENHANCEMENT: Check Rate Limits ---
        if 'X-RateLimit-Remaining' in events_resp.headers:
            remaining = int(events_resp.headers['X-RateLimit-Remaining'])
            if remaining < 10: # Threshold for warning
                 print(f"⚠️ WARNING: Low GitHub API rate limit: {remaining} remaining. Sleeping briefly...")
                 time.sleep(1) # Brief pause before proceeding
            # Optional: Implement logic to stop if remaining is 0

        if events_resp.status_code == 404:
            # User exists, but no public events
            events = []
        else:
            events_resp.raise_for_status()
            events = events_resp.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching GitHub data for {handle}: {e}")
        return None

    # --- ENHANCEMENT: Improved Activity Analysis with Multiple Signals ---
    cutoff_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    recent_pushes = 0
    recent_reviews = 0
    recent_pr_creations = 0
    recent_issue_creations = 0
    repos_contributed_to = set()

    for e in events:
        try:
            # --- FIX 2: Robust Date Parsing ---
            event_time = datetime.fromisoformat(e['created_at'].replace('Z', '+00:00'))
        except (ValueError, KeyError):
            print(f"⚠️ Could not parse date for event {e.get('id')} for user {handle}. Skipping.")
            continue

        if event_time >= cutoff_date:
            repos_contributed_to.add(e.get('repo', {}).get('name', 'unknown_repo'))

            if e['type'] == 'PushEvent':
                recent_pushes += len(e.get('payload', {}).get('commits', []))
            elif e['type'] == 'PullRequestReviewEvent':
                recent_reviews += 1
            elif e['type'] == 'PullRequestEvent' and e.get('payload', {}).get('action') == 'opened':
                recent_pr_creations += 1
            elif e['type'] == 'IssuesEvent' and e.get('payload', {}).get('action') == 'opened':
                recent_issue_creations += 1

    # --- ENHANCEMENT: Nuanced Status Logic based on multiple signals ---
    member_events = []
    activity_score = (
        recent_pushes * 2 + # Weight pushes slightly higher
        recent_pr_creations * 1.5 +
        recent_reviews * 1 +
        recent_issue_creations * 0.5
    )

    if activity_score >= 15: # Higher threshold for Senior
        status = "🟢 VERIFIED SENIOR BUILDER"
        recommendation = "Fast-track to technical interview"
        strength = f"High activity ({recent_pushes} commits, {recent_pr_creations} PRs, {recent_reviews} reviews in 2024–2025)"
    elif activity_score >= 5: # Mid threshold
        status = "🟢 VERIFIED BUILDER"
        recommendation = "Schedule technical screen"
        strength = f"Solid activity ({recent_pushes} commits, {recent_pr_creations} PRs in 2024–2025)"
    elif recent_pushes >= 1 or recent_pr_creations >= 1 or recent_reviews >= 1:
        status = "⚠️ NUANCED POTENTIAL"
        recommendation = "Request live coding sample or detailed project discussion"
        strength = f"Basic activity ({recent_pushes} commits, {recent_pr_creations} PRs, {recent_reviews} reviews in 2024–2025)"
    else:
        # Check for MemberEvent as proxy for private activity (from previous versions)
        member_events = [
            e for e in events
            if e['type'] == 'MemberEvent' and datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')) >= cutoff_date
        ]
        if member_events:
             status = "⚠️ NUANCED POTENTIAL (Active in Org/Private)"
             recommendation = "Investigate further (likely active in private repos)"
             strength = f"Signs of private/org activity ({len(member_events)} MemberEvents in 2024–2025)"
        else:
            status = "🔴 GHOST DEVELOPER"
            recommendation = "Pass or request proof of recent code"
            strength = "No significant public activity in 2024–2025"


    card = (
        f"**{status}** — {user.get('name') or user['login']} (@{user['login']})\n\n"
        f"**📊 Stats:** {user.get('public_repos', 0)} repos | {user.get('followers', 0)} followers\n"
        f"**💻 Activity Score:** ~{activity_score:.1f} (Pushes: {recent_pushes}, PRs: {recent_pr_creations}, Reviews: {recent_reviews}, Issues: {recent_issue_creations})\n"
        f"**🌐 Repos Contributed:** {len(repos_contributed_to)}\n"
        f"**🧠 Assessment:** {strength}\n"
        "----------------------------------\n"
        f"**👮 Recommendation:** {recommendation}\n"
        "----------------------------------\n"
        f"**🔗 Source:** [{user['html_url']}]({user['html_url']})\n\n"
        f"_AI Talent Scout • {datetime.now().strftime('%H:%M on %d %B %Y')}_"
    )

    return {
        "card": card,
        "user": user,
        "status": status.split()[0],  # 🟢/⚠️/🔴
        "activity_score": activity_score,
        "pushes": recent_pushes,
        "prs": recent_pr_creations,
        "reviews": recent_reviews,
        "issues": recent_issue_creations,
        "repos_contributed": len(repos_contributed_to),
        "member_events": len(member_events)
    }

# ========================
# HubSpot Update
# ========================
def post_to_hubspot(email: str, card: str) -> None:
    if not HUBSPOT_CLIENT:
        print("🖨️ Dry run: HubSpot skipped (HUBSPOT_TOKEN not set)")
        print(f"--- Would post to: {email} ---\n{card}\n--- End Note ---")
        return

    search = PublicObjectSearchRequest(
        filter_groups=[FilterGroup(filters=[Filter(property_name="email", operator="EQ", value=email)])],
        limit=1
    )

    try:
        results = HUBSPOT_CLIENT.crm.contacts.search_api.do_search(public_object_search_request=search).results
        if not results:
            print(f"⚠️ Contact not found in HubSpot: {email}")
            return

        contact_id = results[0].id
        note = SimplePublicObjectInputForCreate(
            properties={
                "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                "hs_note_body": card
            },
            associations=[{
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}] # Note-to-Contact association
            }]
        )

        HUBSPOT_CLIENT.crm.objects.notes.basic_api.create(simple_public_object_input_for_create=note)
        print(f"✅ Posted to HubSpot contact {contact_id}: {email}")

    except ApiError as e: # Catch HubSpot-specific errors
        print(f"❌ HubSpot API error for {email}: {e.reason} - {e}")
    except Exception as e: # Catch other potential errors
        print(f"❌ Unexpected error posting to HubSpot for {email}: {e}")

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    # Example list - replace with dynamic fetch in production
    candidates = [
        {"handle": "torvalds", "email": "test-torvalds@yourcompany.com"},
        {"handle": "defunkt", "email": "test-defunkt@yourcompany.com"},
        {"handle": "mojombo", "email": "test-mojombo@yourcompany.com"},
        {"handle": "nonexistentuser123456", "email": "test-fake@yourcompany.com"}, # Test missing user
    ]

    print("🚀 AI Talent Scout v5 Enhanced Running\n")

    for cand in candidates:
        print(f"🔍 Auditing {cand['handle']}...")
        result = audit_github(cand["handle"])
        if result:
            print(result["card"])
            print("-" * 60 + "\n")
            post_to_hubspot(cand["email"], result["card"])
        else:
            print(f"❌ Skipping {cand['handle']} due to audit failure.\n")

    print("🎯 Audit Complete")
