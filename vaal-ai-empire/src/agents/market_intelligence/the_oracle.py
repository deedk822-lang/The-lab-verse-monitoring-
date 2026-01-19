# agents/market_intelligence/the_oracle.py
import requests
import os

# ⚡ Bolt Optimization: Use a requests.Session for connection pooling
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
    "Content-Type": "application/json"
})

def get_perplexity_insight(query):
    """
    Gets market insights from the Perplexity API.
    Uses a shared session for performance.
    """
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro", # The Pro Model
        "messages": [
            {
                "role": "system",
                "content": "You are a Market Intelligence Officer for the Vaal AI Empire. Identify sellable gaps in the South African market based on recent news."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }

    # Use the session to make the request
    response = session.post(url, json=payload)
    response.raise_for_status() # Raise an exception for bad status codes
    return response.json()['choices'][0]['message']['content']
