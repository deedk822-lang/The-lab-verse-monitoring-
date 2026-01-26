# agents/market_intelligence/the_oracle.py
import os
from vaal_ai_empire.api.sanitizers import sanitize_prompt
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_session


def get_perplexity_insight(query: str) -> str:
    """
    Get market intelligence insights from Perplexity AI.

    Args:
        query: The search query to analyze for market gaps.

    Returns:
        The generated insight text from the model.
    """
    secure_session = create_ssrf_safe_session()
    sanitized_query = sanitize_prompt(query)
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro",  # The Pro Model
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Market Intelligence Officer for the Vaal AI Empire. "
                    "Identify sellable gaps in the South African market based on recent news."
                ),
            },
            {"role": "user", "content": sanitized_query},
        ],
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json",
    }

    response = secure_session.post(url, json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"]
