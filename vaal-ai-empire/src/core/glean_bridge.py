import os
import httpx
import logging

logger = logging.getLogger("GleanBridge")

class GleanContextLayer:
    """
    Real implementation of Enterprise Search using Glean/MCP.
    """
    def __init__(self):
        self.endpoint = os.getenv("GLEAN_API_ENDPOINT")
        self.api_key = os.getenv("GLEAN_API_KEY")
        self.is_active = bool(self.endpoint and self.api_key)

    def search_enterprise_memory(self, query: str, context_filter: str = None):
        """
        Executes a real POST request to the Glean Search API.
        """
        if not self.is_active:
            logger.warning("⚠️ Glean Bridge Offline (Missing GLEAN_API_ENDPOINT or GLEAN_API_KEY)")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "source_filters": [context_filter] if context_filter else [],
            "page_size": 3
        }

        try:
            logger.info(f"🔍 Sending Request to Glean: {query}")
            response = httpx.post(f"{self.endpoint}/search", json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # IMPROVEMENT: Log the specific error text from the server
            logger.error(f"❌ Glean API Error ({e.response.status_code}): {e.response.text}")
            return None

        except Exception as e:
            logger.error(f"❌ Glean Connection Failed: {e}")
            return None
