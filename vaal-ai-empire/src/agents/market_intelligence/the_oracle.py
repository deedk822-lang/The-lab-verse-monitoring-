# agents/market_intelligence/the_oracle.py
import os

import requests


def get_perplexity_insight(query):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro",  # The Pro Model
        "messages": [
            {
                "role": "system",
                "content": "You are a Market Intelligence Officer for the Vaal AI Empire. Identify sellable gaps in the South African market based on recent news.",
            },
            {"role": "user", "content": query},
        ],
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"]
