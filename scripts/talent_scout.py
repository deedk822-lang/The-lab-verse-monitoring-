import os
import requests
from datetime import datetime, timezone

# --- CONFIGURATION ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN environment variable is missing.")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_github_user_data(github_handle):
    """
    Fetches user profile and recent public events.
    """
    # FIX: Corrected URL Concatenation (Removed fatal space)
    user_url = f"https://api.github.com/users/{github_handle}" # Fixed URL
    events_url = f"https://api.github.com/users/{github_handle}/events/public" # Fixed URL

    try:
        user_resp = requests.get(user_url, headers=HEADERS)
        user_resp.raise_for_status()
        user_data = user_resp.json()

        events_resp = requests.get(events_url, headers=HEADERS)
        if 'X-RateLimit-Remaining' in events_resp.headers:
            remaining = int(events_resp.headers['X-RateLimit-Remaining'])
            if remaining < 10:
                print(f"⚠️ WARNING: Only {remaining} API calls remaining. Sleeping/Stopping recommended.")
        events_resp.raise_for_status()
        events = events_resp.json()

        return user_data, events

    except requests.exceptions.RequestException as e:
        print(f"API Error for {github_handle}: {e}")
        return None, None

def analyze_github_activity(events):
    """
    Analyzes events to determine seniority and recent activity.
    Improved logic with more event types and nuanced scoring.
    """
    cutoff_date = datetime(2024, 1, 1, tzinfo=timezone.utc) # Updated cutoff

    scores = {
        'commits': 0,
        'reviews': 0,
        'prs_created': 0,
        'prs_reviewed': 0,
        'issues_created': 0,
        'issues_commented': 0,
        'releases': 0,
        'forks': 0, # Could indicate contributing interest
        'gists': 0, # Less common, but shows code snippets
        'complexity_signals': 0,
        'contributed_repos': set() # Track distinct repos
    }

    for e in events:
        created_at_str = e.get('created_at')
        if not created_at_str:
            continue # Skip if no timestamp
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        except ValueError:
            print(f"Warning: Could not parse date {created_at_str} for event type {e.get('type')}. Skipping.")
            continue

        if created_at < cutoff_date:
            continue # Skip events before cutoff

        event_type = e.get('type')
        repo_name = e.get('repo', {}).get('name', 'unknown_repo')
        scores['contributed_repos'].add(repo_name)

        # --- Scoring based on event type ---
        if event_type == 'PushEvent':
            commit_count = len(e.get('payload', {}).get('commits', []))
            scores['commits'] += commit_count
            # Check for complexity in commit messages or filenames (basic heuristic)
            for commit in e.get('payload', {}).get('commits', []):
                message = commit.get('message', '').lower()
                if any(keyword in message for keyword in ['refactor', 'perf', 'fix', 'feature', 'async', 'microservice', 'architecture']):
                    scores['complexity_signals'] += 1

        elif event_type == 'PullRequestEvent':
            action = e.get('payload', {}).get('action')
            if action == 'opened':
                scores['prs_created'] += 1
            elif action in ['review_requested', 'reviewed']:
                scores['prs_reviewed'] += 1 # Counting PRs they are involved in reviewing

        elif event_type == 'PullRequestReviewEvent':
            scores['reviews'] += 1

        elif event_type == 'IssuesEvent':
            action = e.get('payload', {}).get('action')
            if action == 'opened':
                scores['issues_created'] += 1
            elif action == 'commented':
                scores['issues_commented'] += 1

        elif event_type == 'ReleaseEvent':
            scores['releases'] += 1 # Indicates involvement in shipping

        elif event_type == 'ForkEvent':
            scores['forks'] += 1 # Shows interest in contributing

        elif event_type == 'CreateEvent':
            # Could be creating a branch, tag, or repo. Check ref_type
            ref_type = e.get('payload', {}).get('ref_type')
            if ref_type == 'repository':
                 scores['gists'] += 1 # Assuming CreateEvent for repo counts towards activity
            # Could also count gists if ref_type == 'gist' (though rare)


    # --- Calculate Skill Depth based on scores ---
    total_activity_score = (
        scores['commits'] * 2 +           # Commits are weighted heavily
        scores['prs_created'] * 3 +       # Creating PRs shows initiative
        scores['reviews'] * 2 +           # Reviewing shows understanding
        scores['prs_reviewed'] * 1 +      # Being involved in PRs
        scores['issues_created'] * 1 +    # Reporting issues shows engagement
        scores['issues_commented'] * 0.5 + # Commenting is good
        scores['releases'] * 5 +          # Shipping releases is high value
        scores['complexity_signals'] * 3  # Heuristic for complex work
    )

    # Adjust score based on number of distinct repositories contributed to (diversity)
    repo_diversity_bonus = min(len(scores['contributed_repos']) - 1, 3) # Cap bonus
    total_activity_score += repo_diversity_bonus * 2

    # Determine level based on score thresholds
    if total_activity_score >= 100:
        skill_level = "Senior (Architect/Lead)"
    elif total_activity_score >= 50:
        skill_level = "Senior (Experienced)"
    elif total_activity_score >= 20:
        skill_level = "Mid (Solid Contributor)"
    elif total_activity_score >= 5:
        skill_level = "Mid (Learning & Contributing)"
    elif total_activity_score > 0:
        skill_level = "Junior (Active Learner)"
    else:
        # Check for MemberEvent or other signs of private activity (from original logic)
        member_events = [e for e in events if e.get('type') == 'MemberEvent' and datetime.fromisoformat(e.get('created_at').replace('Z', '+00:00')) >= cutoff_date]
        if member_events:
            skill_level = "Potential Senior (Active in Org/Private)"
        else:
            skill_level = "Ghost Developer (Low Public Activity)"

    return {
        "total_activity_score": total_activity_score,
        "commits": scores['commits'],
        "prs_created": scores['prs_created'],
        "reviews": scores['reviews'],
        "prs_reviewed": scores['prs_reviewed'],
        "issues_created": scores['issues_created'],
        "issues_commented": scores['issues_commented'],
        "releases": scores['releases'],
        "forks": scores['forks'],
        "complexity_signals": scores['complexity_signals'],
        "repos_contributed_to": len(scores['contributed_repos']),
        "skill_depth": skill_level,
        "status_code": "VERIFIED" if total_activity_score > 0 or len([e for e in events if e.get('type') == 'MemberEvent' and datetime.fromisoformat(e.get('created_at').replace('Z', '+00:00')) >= cutoff_date]) > 0 else "GHOST"
    }

def generate_talent_card(user_data, analysis):
    """
    Formats the final output.
    """
    company = user_data.get('company') or "Unknown"
    bio = user_data.get('bio', 'N/A')[:50] + "..." if user_data.get('bio') else "N/A"
    followers = user_data.get('followers', 0)
    public_repos = user_data.get('public_repos', 0)

    status_emoji = "✅" if analysis['status_code'] == "VERIFIED" else "👻"
    urgency = "24h" if analysis['status_code'] == "VERIFIED" else "72h"

    card = f"""
----------------------------------------------------------------
🚀 TALENT SCOUT V1.1 CARD (Enhanced Skill Logic)
----------------------------------------------------------------
👤 Profile:  {user_data.get('name')} (@{user_data.get('login')})
🏢 Company:  {company}
📝 Bio:      {bio}
🌟 Followers: {followers} | Repos: {public_repos}

🔍 SKILL ANALYSIS (Score: {analysis['total_activity_score']})
----------------------------------------------------------------
📊 Level:    {analysis['skill_depth']}
📥 Commits:  {analysis['commits']}
📝 PRs C:    {analysis['prs_created']} | PRs R: {analysis['prs_reviewed']} | Reviews: {analysis['reviews']}
💬 Issues:   C: {analysis['issues_created']} | Com: {analysis['issues_commented']}
📦 Releases: {analysis['releases']}
🔧 Forks:    {analysis['forks']}
🔍 Complex:  {analysis['complexity_signals']} signals
🌐 Repos:    {analysis['repos_contributed_to']} distinct

⚡ STATUS:   {status_emoji} {analysis['status_code']}
⏱️ ACTION:   Contact within {urgency}
----------------------------------------------------------------
"""
    return card

# --- MAIN EXECUTION FLOW ---
if __name__ == "__main__":
    candidates = ["torvalds", "octocat", "ghost-user-12345"] # Example list

    print(f"--- Starting Talent Scout v1.1 Enhanced Batch ({len(candidates)} candidates) ---\n")

    for handle in candidates:
        print(f"Scanning {handle}...")
        user_data, events = get_github_user_data(handle)

        if user_data and events:
            analysis = analyze_github_activity(events)
            card = generate_talent_card(user_data, analysis)
            print(card)
        else:
            print(f"❌ Failed to retrieve data for {handle}\n")
