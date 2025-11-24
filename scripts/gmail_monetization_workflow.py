# scripts/gmail_monetization_workflow.py

import os
import base64
import json
import logging
from datetime import datetime, timedelta

import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the scopes for the Google APIs you want to access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/linkedin.post',
    'https://www.googleapis.com/auth/wordpress.post'
]

# CData Connect AI / MCP Endpoint
CONNECT_AI_MCP = os.getenv("CONNECT_AI_MCP", "https://mcp.cloud.cdata.com/mcp")

# WordPress Configuration
WORDPRESS_API_URL = os.getenv("WORDPRESS_API_URL", "https://deedk822.wordpress.com/wp-json/wp/v2/posts")
WORDPRESS_USER = os.getenv("WORDPRESS_USER")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

# --- AUTHENTICATION ---

def get_gmail_credentials():
    """Gets valid user credentials from storage or initiates OAuth2 flow."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # IMPORTANT: You must have a 'credentials.json' file from Google Cloud Console
            # for this to work.
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# --- CORE LOGIC ---

def fetch_recent_emails(service, query="is:important is:unread", max_results=5):
    """Fetches recent, important, and unread emails from Gmail."""
    logging.info(f"Fetching up to {max_results} emails with query: '{query}'")
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        email_contents = []
        if not messages:
            logging.info("No new important emails found.")
            return []

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg['payload']
            headers = payload['headers']
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            sender = next(h['value'] for h in headers if h['name'] == 'From')

            # Get the email body
            if 'parts' in payload:
                part = payload['parts'][0]
                data = part['body']['data']
            else:
                data = payload['body']['data']

            body = base64.urlsafe_b64decode(data).decode('utf-8')

            email_contents.append({
                "subject": subject,
                "sender": sender,
                "body": body[:500] # Truncate for brevity
            })
        logging.info(f"Successfully fetched {len(email_contents)} emails.")
        return email_contents
    except Exception as e:
        logging.error(f"An error occurred while fetching emails: {e}")
        return []

def analyze_email_for_monetization(email_content):
    """
    Uses an AI model (via CData Connect AI) to analyze email content and
    generate a monetization plan (e.g., a blog post idea, a social media post).
    """
    logging.info(f"Analyzing email with subject: '{email_content['subject']}'")

    prompt = f"""
    Analyze the following email content and generate a concise, actionable monetization plan.
    The plan should be a single JSON object with two keys: 'wordpress_post' and 'linkedin_post'.

    - 'wordpress_post': A detailed JSON object with 'title' and 'content' for a blog post inspired by the email.
    - 'linkedin_post': A short, engaging string for a LinkedIn post.

    Email Subject: {email_content['subject']}
    Email Sender: {email_content['sender']}
    Email Body Snippet: {email_content['body']}

    Generate the JSON object now.
    """

    try:
        # This conceptual query uses CData to proxy a call to an AI provider like Mistral
        # The actual query format will depend on the CData configuration.
        cdata_query = {
            "query": f"SELECT content FROM Mistral WHERE prompt = '{prompt.replace(\"'\", \"''\")}'"
        }

        # This part is conceptual as we don't have the CData API key.
        # response = requests.post(CONNECT_AI_MCP, json=cdata_query, headers={"Authorization": f"Bearer {os.getenv('CDATA_API_KEY')}"})
        # response.raise_for_status()
        # ai_response = response.json()['data'][0]['content']

        # --- MOCKED AI RESPONSE for demonstration without a live API key ---
        logging.warning("Using mocked AI response for demonstration.")
        mock_ai_response = {
            "wordpress_post": {
                "title": f"New Insights on: {email_content['subject']}",
                "content": f"<p>A recent communication from {email_content['sender']} highlighted a key trend. The core message was: '{email_content['body']}'.</p><p>This is a significant development for the industry. Here’s why this matters and how businesses can capitalize on this trend...</p>"
            },
            "linkedin_post": f"Hot Topic Alert! 🔥 Just unpacked some new insights related to '{email_content['subject']}'. The key takeaway is that the industry is moving towards a more data-driven approach. This reinforces the need for robust analytics and real-time monitoring. #AI #BusinessIntelligence #Innovation"
        }
        ai_response = json.dumps(mock_ai_response)
        # --- END MOCKED AI RESPONSE ---

        logging.info("Successfully generated monetization plan from AI.")
        return json.loads(ai_response)
    except Exception as e:
        logging.error(f"Failed to analyze email with AI: {e}")
        return None

def post_to_wordpress(title, content):
    """Posts content to the configured WordPress site."""
    if not all([WORDPRESS_USER, WORDPRESS_APP_PASSWORD]):
        logging.error("WordPress credentials are not set. Skipping post.")
        return None

    logging.info(f"Posting to WordPress: '{title}'")
    auth_string = f"{WORDPRESS_USER}:{WORDPRESS_APP_PASSWORD}"
    headers = {
        'Authorization': f'Basic {base64.b64encode(auth_string.encode()).decode()}',
        'Content-Type': 'application/json'
    }
    payload = {
        'title': title,
        'content': content,
        'status': 'draft' # Post as a draft for review
    }
    try:
        response = requests.post(WORDPRESS_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Successfully created WordPress draft with ID: {response.json()['id']}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post to WordPress: {e}")
        return None

def main():
    """Main execution function for the Gmail monetization workflow."""
    logging.info("--- Starting Gmail Monetization Workflow ---")

    # 1. Authenticate and get Gmail service
    gmail_creds = get_gmail_credentials()
    if not gmail_creds:
        logging.error("Failed to obtain Gmail credentials. Exiting.")
        return
    gmail_service = build('gmail', 'v1', credentials=gmail_creds)

    # 2. Fetch recent emails
    emails = fetch_recent_emails(gmail_service)

    if not emails:
        logging.info("--- Workflow complete: No new emails to process. ---")
        return

    # 3. Process each email
    for email in emails:
        # 4. Analyze email for monetization opportunities
        monetization_plan = analyze_email_for_monetization(email)

        if not monetization_plan:
            continue

        # 5. Execute the monetization plan
        # Post to WordPress
        if 'wordpress_post' in monetization_plan:
            wp_data = monetization_plan['wordpress_post']
            post_to_wordpress(wp_data['title'], wp_data['content'])

        # Post to LinkedIn (conceptual - would require a LinkedIn API library)
        if 'linkedin_post' in monetization_plan:
            logging.info(f"LinkedIn Post Generated: '{monetization_plan['linkedin_post']}'")
            # In a real scenario, you would use a LinkedIn API client here.

    logging.info("--- Gmail Monetization Workflow Finished ---")


if __name__ == '__main__':
    main()
