import os
import sys
from datetime import datetime
from jira import JIRA
from notion_client import Client

# --- CONFIGURATION ---
# Load credentials from environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USER_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

def validate_env_vars():
    """Ensure all required environment variables are set."""
    required_vars = {
        "NOTION_API_KEY": NOTION_API_KEY,
        "NOTION_PAGE_ID": NOTION_PAGE_ID,
        "JIRA_URL": JIRA_URL,
        "JIRA_USER_EMAIL": JIRA_USER_EMAIL,
        "JIRA_API_TOKEN": JIRA_API_TOKEN,
        "JIRA_PROJECT_KEY": JIRA_PROJECT_KEY,
    }
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        print("Please set them before running the script.", file=sys.stderr)
        sys.exit(1)
    print("✅ All environment variables are loaded.")

def get_jira_issues(jira_client):
    """Fetch the 5 most recently updated issues from the specified Jira project."""
    try:
        print(f"🔍 Searching for issues in project '{JIRA_PROJECT_KEY}'...")
        # JQL to find the 5 most recently updated issues in the project
        jql_query = f'project = "{JIRA_PROJECT_KEY}" ORDER BY updated DESC'
        issues = jira_client.search_issues(jql_query, maxResults=5)
        if not issues:
            print("🟡 No issues found in the project.")
            return []
        print(f"✅ Found {len(issues)} issues.")
        return issues
    except Exception as e:
        print(f"❌ Error fetching Jira issues: {e}", file=sys.stderr)
        sys.exit(1)

def create_notion_page(notion_client, issues):
    """Create a new Notion page with a summary of the Jira issues."""
    if not issues:
        print("Skipping Notion page creation as there are no issues to report.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = f"Jira Project '{JIRA_PROJECT_KEY}' Summary - {today_str}"

    print(f"📄 Creating Notion page with title: '{title}'")

    # Construct Notion page content
    children_blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": title}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Here is a summary of the 5 most recently updated issues:"}}]}
        },
    ]

    for issue in issues:
        issue_url = f"{JIRA_URL}/browse/{issue.key}"
        issue_summary = (
            f"[{issue.key}] {issue.fields.summary} "
            f"(Status: {issue.fields.status.name}, "
            f"Updated: {issue.fields.updated.split('T')[0]})"
        )
        children_blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"type": "text", "text": {"content": issue_summary, "link": {"url": issue_url}}}
                ]
            }
        })

    try:
        response = notion_client.pages.create(
            parent={"page_id": NOTION_PAGE_ID},
            properties={"title": [{"type": "text", "text": {"content": title}}]},
            children=children_blocks
        )
        print(f"✅ Successfully created Notion page!")
        print(f"   -> URL: {response['url']}")
    except Exception as e:
        print(f"❌ Error creating Notion page: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to run the authority pipeline."""
    print("🚀 Starting the Authority Pipeline...")
    validate_env_vars()

    # Initialize API clients
    try:
        jira_client = JIRA(
            server=JIRA_URL,
            basic_auth=(JIRA_USER_EMAIL, JIRA_API_TOKEN)
        )
        notion_client = Client(auth=NOTION_API_KEY)
        print("✅ Successfully connected to Jira and Notion APIs.")
    except Exception as e:
        print(f"❌ API Client Initialization Failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Run the pipeline
    issues = get_jira_issues(jira_client)
    create_notion_page(notion_client, issues)

    print("🏁 Pipeline finished successfully.")

if __name__ == "__main__":
    main()
