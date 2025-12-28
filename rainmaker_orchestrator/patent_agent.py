# rainmaker_orchestrator/patent_agent.py

import aiohttp
import json
from typing import Dict, List, Any

class PatentAgent:
    """
    Patent research agent using open APIs + free/permitted sources.
    Does NOT scrape Perplexity or other closed UIs.
    """

    def __init__(self):
        self.google_patents_url = "https://patents.google.com/"
        self.patentsview_url = "https://www.patentsview.org/api/patents/query"
        self.lens_api_url = "https://lens-api.lens.org/patent/search"

    async def search_google_patents_via_structured_data(
        self,
        query: str,
        cpc_code: str = None
    ) -> Dict[str, Any]:
        """
        Query Google Patents using their JSON endpoint (no scraping).
        Google explicitly permits research use of their patent data.
        """
        # Google Patents exposes structured data via JSON endpoints
        params = {
            "q": query,
            "sort": "date",
            "page": 1
        }

        if cpc_code:
            params["cpc"] = cpc_code  # e.g., "H04L" for data processing

        # Note: Google Patents doesn't have a direct JSON API, but you can
        # use PatentsView or Lens instead (see below)
        return {"status": "info", "message": "Use PatentsView or Lens API for structured data"}

    async def search_patentsview_api(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query USPTO PatentsView API (free, open, no ToS violation).
        Returns structured patent data.
        """
        # PatentsView API documentation: https://www.patentsview.org/api/

        payload = {
            "q": {
                "patent_abstract": {"text": query}
            },
            "f": [
                "patent_id",
                "patent_title",
                "patent_abstract",
                "patent_date",
                "assignee_name",
                "ipc_classification",
                "uspc_classification"
            ],
            "size": limit,
            "sort": [{"patent_date": "desc"}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.patentsview_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "success",
                            "source": "patentsview",
                            "query": query,
                            "count": len(data.get("patents", [])),
                            "patents": [
                                {
                                    "id": p.get("patent_id"),
                                    "title": p.get("patent_title"),
                                    "abstract": p.get("patent_abstract"),
                                    "date": p.get("patent_date"),
                                    "assignee": p.get("assignee_name")[0].get("assignee_name") if p.get("assignee_name") else None,
                                    "ipc": p.get("ipc_classification")[0].get("ipc_classification") if p.get("ipc_classification") else None
                                }
                                for p in data.get("patents", [])
                            ]
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"PatentsView API returned {resp.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def search_lens_api(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query Lens.org Patent Search API (free for research).
        Returns rich patent landscape data.
        """
        # Lens API is free for non-commercial research
        # Docs: https://lens.org/lens-api/lens-api-overview

        payload = {
            "query": {
                "simple_query": query
            },
            "size": limit,
            "sort": [{"date_published": "desc"}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.lens_api_url}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "success",
                            "source": "lens",
                            "query": query,
                            "count": data.get("total", 0),
                            "results": data.get("data", [])
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Lens API error: {resp.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def novelty_check(self, invention_description: str) -> Dict[str, Any]:
        """
        Assess patent novelty: search for similar patents and determine gaps.
        Uses multiple open sources for comprehensive landscape analysis.
        """
        # Extract key technical terms from description
        key_terms = self._extract_terms(invention_description)

        results = {
            "invention": invention_description[:200],
            "key_terms": key_terms,
            "sources": {}
        }

        # Search each source
        for term in key_terms[:3]:  # Top 3 terms
            pv_result = await self.search_patentsview_api(term, limit=5)
            if pv_result["status"] == "success":
                results["sources"]["patentsview"] = pv_result

            lens_result = await self.search_lens_api(term, limit=5)
            if lens_result["status"] == "success":
                results["sources"]["lens"] = lens_result

        return {
            "status": "success",
            "task": "novelty_check",
            "findings": results,
            "recommendation": self._assess_novelty(results)
        }

    def _extract_terms(self, text: str) -> List[str]:
        """Extract technical keywords for patent search."""
        # Simple extraction; in production, use NLP (spacy, BERT)
        stop_words = {"a", "the", "and", "or", "in", "for", "is", "of"}
        words = text.lower().split()
        return [w for w in words if len(w) > 4 and w not in stop_words]

    def _assess_novelty(self, findings: Dict[str, Any]) -> str:
        """Synthesize novelty assessment from patent search results."""
        total_similar = (
            findings["sources"].get("patentsview", {}).get("count", 0) +
            findings["sources"].get("lens", {}).get("count", 0)
        )

        if total_similar == 0:
            return "HIGH novelty: No similar patents found in USPTO/Lens databases"
        elif total_similar < 5:
            return "MODERATE novelty: Few similar patents; differentiation likely possible"
        elif total_similar < 20:
            return "LOW novelty: Multiple similar patents exist; careful claim drafting needed"
        else:
            return "VERY LOW novelty: Patent landscape saturated; consider alternative approaches"
