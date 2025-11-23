import requests
import pandas as pd
from io import StringIO
import datetime
import json
import os

# --- CONFIGURATION ---
# GDELT V2 GKG (Global Knowledge Graph) API endpoint. This is a public, factual endpoint.
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# GDELT themes related to hardship, poverty, and displacement.
# These are official GDELT themes.
DISTRESS_THEMES = [
    "TAX_FNCACT_REFUGEE", "WB_2749_FOOD_CRISIS", "UNGP_FORCED_DISPLACEMENT",
    "TAX_ETHNICVIOLENCE", "CRISISLEX_C07_INSECURITY", "POVERTY"
]

def find_events_of_hardship():
    """
    Queries the GDELT API to find recent news articles in Africa
    matching themes of hardship.
    """
    print("[TAX COLLECTOR] Searching for real-world hardship events in Africa...")
    
    # Build a complex query for GDELT
    themes_query = " OR ".join([f'theme:"{t}"' for t in DISTRESS_THEMES])
    
    # Filter for Africa and recent events (last 24 hours)
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    
    query_params = {
        "query": f'({themes_query}) sourcecountry:AFRICA',
        "mode": "ArtList",
        "maxrecords": 5,
        "format": "json",
        "timespan": "24h"
    }
    
    try:
        response = requests.get(GDELT_API_URL, params=query_params)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articles', [])
        
        if not articles:
            print("[TAX COLLECTOR] No recent hardship events found in Africa.")
            return []

        print(f"[TAX COLLECTOR] Found {len(articles)} recent hardship events.")
        
        # Extract key information
        hardship_events = []
        for article in articles:
            hardship_events.append({
                "title": article.get('title'),
                "url": article.get('url'),
                "source": article.get('source'),
                "date": article.get('date')
            })
            
        return hardship_events
        
    except requests.exceptions.RequestException as e:
        print(f"[TAX COLLECTOR] Error querying GDELT API: {e}")
        return []

def collect_tax(content_keyword: str):
    """
    The main function for the Tax Collector.
    It finds a hardship event and generates a 'tax' message.
    """
    events = find_events_of_hardship()
    
    if not events:
        print("[TAX COLLECTOR] Tax collection skipped: No events found.")
        return "Tax collection skipped: No recent hardship events found to report."

    # Pick the most recent event
    event = events[0]
    
    # The 'tax' is a message that contextualizes the generated content
    # with a real-world issue.
    tax_message = f"""
    --- THE TAX COLLECTOR'S REPORT ---
    
    Your content on '{content_keyword}' has been successfully generated and distributed.
    
    However, the system's conscience requires you to acknowledge a real-world issue:
    
    **Hardship Event:** {event['title']}
    **Source:** {event['source']}
    **Date:** {event['date']}
    **Read More:** {event['url']}
    
    This report serves as a reminder of the global context and the purpose of the system's success.
    --- END OF REPORT ---
    """
    
    print("[TAX COLLECTOR] Tax collected successfully.")
    return tax_message

if __name__ == "__main__":
    # Example usage: The keyword from the content generation run
    # In the actual workflow, this will be passed as an argument.
    example_keyword = os.environ.get("CONTENT_KEYWORD", "AI in Content Creation")
    tax_report = collect_tax(example_keyword)
    
    # The GitHub Action will capture this output
    print(f"::set-output name=tax_report::{tax_report}")
    print(tax_report)
