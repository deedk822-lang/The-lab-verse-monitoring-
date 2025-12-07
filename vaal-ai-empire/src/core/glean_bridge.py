import os
import httpx
import logging
import json

# Setup Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("GleanBridge")

class GleanContextLayer:
    """
    The Bridge between the Agent and the Enterprise Data.
    Uses Glean MCP to fetch 'Permission-Aware' answers.
    """
    def __init__(self):
        self.endpoint = os.getenv("GLEAN_API_ENDPOINT")
        self.api_key = os.getenv("GLEAN_API_KEY")

        # If no endpoint is set, we use a mock for CI/Dev to prevent crashing
        self.is_active = bool(self.endpoint and self.api_key)

    def search_enterprise_memory(self, query: str, context_filter: str = None):
        """
        WHY: To ground the Agent's decisions in internal company reality.
        HOW: Query Glean via REST/MCP.
        """
        if not self.is_active:
            logger.warning("⚠️ Glean Bridge inactive. Using local intuition only.")
            return "No internal records found (Bridge Offline)."

        logger.info(f"🔍 SEARCHING ENTERPRISE GRAPH: '{query}'")

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
            # This simulates the MCP tool call to the Glean Server
            response = httpx.post(f"{self.endpoint}/search", json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Parse the "Blended" result (Structured + Unstructured)
                summary = data.get('summary', 'No summary available.')
                citations = len(data.get('results', []))

                logger.info(f"✅ Found {citations} internal documents.")
                return summary
            else:
                logger.error(f"❌ Glean Error: {response.text}")
                return "Error retrieving internal data."

        except Exception as e:
            logger.error(f"❌ Connection Failed: {e}")
            return "Connection to Enterprise Graph failed."

    def get_customer_360(self, customer_id):
        """
        Example Use Case: Sentinel Agent checking a client's risk profile.
        Combines CRM (Salesforce) + Tickets (Jira) + Usage (Databricks).
        """
        return self.search_enterprise_memory(
            query=f"Show me everything about customer {customer_id}",
            context_filter="customer_360"
        )
