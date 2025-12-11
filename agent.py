#!/usr/bin/env python3
"""
Google-Apps-Aware Distribution Agent
Reads your real app list & services → picks best channel per post.
Zero API keys in repo – ADC only.
"""

import argparse
import json
import logging
import os
import sys
import time
import hashlib
import pathlib
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Optional

# Configure logging
LOG = logging.getLogger("AppsAgent")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())
LOG.addHandler(RotatingFileHandler(
    "distribution.log", 
    maxBytes=5*1024*1024, 
    backupCount=5, 
    encoding="utf-8"
))

# Track sent posts to avoid duplicates
LEDGER = pathlib.Path("sent.json")
SENT_CACHE = set(json.loads(LEDGER.read_text()) if LEDGER.exists() else "[]")

@dataclass
class Post:
    text: str
    media: List[pathlib.Path]

# --- Google ADC Setup ---
def _google_creds() -> tuple:
    """Fetch Google Application Default Credentials (ADC)."""
    import google.auth
    creds, project = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/business.manage",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/calendar"
        ]
    )
    return creds, project

# --- Discover Available Google Services ---
def _discover_services(creds) -> Dict[str, bool]:
    """Detect which Google services are available and accessible."""
    from googleapiclient.discovery import build
    services = {}

    # Check Gmail
    try:
        gmail = build("gmail", "v1", credentials=creds)
        gmail.users().getProfile(userId="me").execute()
        services["Gmail"] = True
    except Exception:
        services["Gmail"] = False

    # Check Google Business Profile
    try:
        gbp = build("mybusinessbusinessinformation", "v1", credentials=creds)
        accounts = gbp.accounts().list().execute()
        services["GoogleBusiness"] = bool(accounts.get("accounts"))
    except Exception:
        services["GoogleBusiness"] = False

    # Check YouTube
    try:
        yt = build("youtube", "v3", credentials=creds)
        yt.channels().list(mine=True, part="id").execute()
        services["YouTube"] = True
    except Exception:
        services["YouTube"] = False

    # Check Calendar
    try:
        cal = build("calendar", "v3", credentials=creds)
        cal.calendarList().list(maxResults=1).execute()
        services["Calendar"] = True
    except Exception:
        services["Calendar"] = False

    LOG.info("Discovered Google services: %s", [k for k, v in services.items() if v])
    return services

# --- Smart Channel Selection ---
def _choose_channel(services: Dict[str, bool], post: Post) -> str:
    """Select the best channel for the post based on content and available services."""
    if services.get("GoogleBusiness") and len(post.text) < 1500:
        return "GoogleBusiness"
    if services.get("YouTube") and post.media and post.media[0].suffix.lower() in (".mp4", ".mov"):
        return "YouTube"
    if services.get("Calendar") and "#event" in post.text.lower():
        return "Calendar"
    if services.get("Gmail"):
        return "Gmail"
    return "AyrShare"  # Fallback

# --- Channel-Specific Posting Logic ---
def _send_gmail(creds, post: Post) -> str:
    """Post to Gmail."""
    from googleapiclient.discovery import build
    from email.mime.text import MIMEText
    import base64
    
    gmail = build("gmail", "v1", credentials=creds)
    msg = MIMEText(post.text)
    msg["To"] = os.getenv("FALLBACK_EMAIL", "you@yourdomain.com")
    msg["From"] = "agent@yourdomain.com"
    msg["Subject"] = "Agent Update"
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"gmail-{result['id']}"

def _send_google_business(creds, post: Post) -> str:
    """Post to Google Business Profile."""
    from googleapiclient.discovery import build
    
    gbp = build("mybusinessbusinessinformation", "v1", credentials=creds)
    accounts = gbp.accounts().list().execute()
    location = accounts["accounts"][0]["name"]
    
    posts_service = build("mybusinessbusinessposts", "v1", credentials=creds)
    body = {"summary": post.text[:1500], "topicType": "STANDARD"}
    result = posts_service.locations().localPosts().create(parent=location, body=body).execute()
    return f"gbp-{result['name']}"

def _send_youtube(creds, post: Post) -> str:
    """Post to YouTube (as a community post)."""
    from googleapiclient.discovery import build
    
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "type": "upload",
            "title": post.text[:60],
            "description": post.text
        }
    }
    result = yt.activities().insert(part="snippet", body=body).execute()
    return f"yt-{result['id']}"

def _send_calendar(creds, post: Post) -> str:
    """Add an event to Google Calendar."""
    from googleapiclient.discovery import build
    
    cal = build("calendar", "v3", credentials=creds)
    result = cal.events().quickAdd(calendarId="primary", text=post.text).execute()
    return f"cal-{result['id']}"

def _send_ayrshare(api_key: str, post: Post) -> str:
    """Fallback: Post via AyrShare."""
    import requests
    
    payload = {
        "post": post.text,
        "platforms": ["twitter", "linkedin", "facebook", "instagram"]
    }
    if post.media:
        payload["mediaUrls"] = [str(m) for m in post.media]
    
    response = requests.post(
        "https://app.ayrshare.com/api/post",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload
    )
    response.raise_for_status()
    return f"ayr-{response.json().get('id', 'ok')}"

# --- Load Content ---
def load_content(source: str) -> List[Post]:
    """Load posts from a file or directory."""
    src = pathlib.Path(source)
    if not src.exists():
        LOG.error("Source %s not found", source)
        return []
    
    if src.is_file():
        return [Post(text=src.read_text(encoding="utf-8"), media=[])]
    
    # Directory mode: Load all .txt files and associated media
    posts = []
    for txt_file in sorted(src.glob("*.txt")):
        media = [
            m for m in txt_file.with_suffix("").glob("*")
            if m.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4")
        ]
        posts.append(Post(
            text=txt_file.read_text(encoding="utf-8"),
            media=media
        ))
    
    LOG.info("Loaded %d posts from %s", len(posts), src)
    return posts

# --- Update Ledger ---
def _update_ledger(post_id: str) -> None:
    """Track sent posts to avoid duplicates."""
    SENT_CACHE.add(post_id)
    LEDGER.write_text(json.dumps(list(SENT_CACHE)))

# --- Main Workflow ---
def main():
    parser = argparse.ArgumentParser(description="Google-Apps-Aware Distribution Agent")
    parser.add_argument("--content", required=True, help="File or directory with content")
    parser.add_argument("--config", default="config.json", help="Unused (kept for compatibility)")
    args = parser.parse_args()
    
    # Initialize Google credentials
    creds, project = _google_creds()
    
    # Load posts
    posts = load_content(args.content)
    if not posts:
        LOG.error("No content to distribute")
        sys.exit(1)
    
    # Discover available services
    services = _discover_services(creds)
    
    # Fetch AyrShare key (fallback)
    ayr_key = ""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        ayr_key = client.access_secret_version(
            request={"name": f"projects/{project}/secrets/ayrshare-api-key/versions/latest"}
        ).payload.data.decode("UTF-8")
        LOG.info("AyrShare fallback enabled")
    except Exception as e:
        LOG.warning("AyrShare key not found: %s", e)
    
    # Distribute posts
    for post in posts:
        post_id = hashlib.sha256(post.text.encode()).hexdigest()[:16]
        if post_id in SENT_CACHE:
            LOG.info("Skipping duplicate post: %s", post_id)
            continue
        
        channel = _choose_channel(services, post)
        LOG.info("Selected channel: %s for post: %s", channel, post.text[:50])
        
        try:
            if channel == "Gmail":
                url = _send_gmail(creds, post)
            elif channel == "GoogleBusiness":
                url = _send_google_business(creds, post)
            elif channel == "YouTube":
                url = _send_youtube(creds, post)
            elif channel == "Calendar":
                url = _send_calendar(creds, post)
            else:  # Fallback to AyrShare
                if not ayr_key:
                    raise RuntimeError("No AyrShare key and no suitable Google channel")
                url = _send_ayrshare(ayr_key, post)
            
            LOG.info("✅ Posted to %s: %s", channel, url)
        except Exception as e:
            LOG.error("❌ Failed to post to %s: %s", channel, e)
        
        _update_ledger(post_id)
    
    LOG.info("Distribution complete. Logs: distribution.log")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOG.info("Aborted by user")
        sys.exit(0)