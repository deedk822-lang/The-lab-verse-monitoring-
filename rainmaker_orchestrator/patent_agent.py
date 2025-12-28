import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import aiohttp
from aiohttp import ClientSession, ClientTimeout, BasicAuth
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio

logger = logging.getLogger(__name__)

class PatentAgent:
    """
    Patent agent with connection pooling, normalized schema, and Lens API integration.
    Uses aiohttp.ClientSession as a context manager for proper connection reuse.
    """

    LENS_API_URL = "https://api.lens.org/patent/search"
    PATENTVIEW_API_URL = "https://search.patentsview.org/api/v1/patent"

    def __init__(self):
        self.session = None
        self.lens_token = None
        self.timeout = ClientTimeout(total=30, connect=10, sock_read=20)

    async def __aenter__(self):
        """Async context manager entry - creates pooled session"""
        self.lens_token = self._get_lens_token()
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ttl_dns_cache=300)
        self.session = ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'RainmakerOrchestrator/1.0'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes session properly"""
        if self.session:
            await self.session.close()

    def _get_lens_token(self) -> str:
        """Safely retrieve Lens API token from environment"""
        import os
        token = os.getenv('LENS_API_TOKEN')
        if not token:
            raise ValueError("LENS_API_TOKEN environment variable not set")
        if len(token) < 20:  # Basic validation
            raise ValueError("Invalid LENS_API_TOKEN format")
        return token.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _call_lens_api(self, query: str) -> Dict[str, Any]:
        """Call Lens API with retry logic and connection pooling"""
        if not self.session:
            raise RuntimeError("PatentAgent session not initialized. Use as async context manager.")

        headers = {
            'Authorization': f'Bearer {self.lens_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "query": {
                "match": {
                    "title": {
                        "query": query,
                        "operator": "AND"
                    }
                }
            },
            "size": 50,
            "include": [
                "lens_id", "publication_number", "title", "abstract", "filing_date",
                "grant_date", "inventors", "assignees", "citations", "jurisdictions"
            ]
        }

        try:
            async with self.session.post(
                self.LENS_API_URL,
                json=payload,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 401:
                    raise PermissionError("Lens API authentication failed - invalid or expired token")
                if response.status >= 400:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=f"Lens API error: {error_text}",
                        headers=response.headers
                    )

                return await response.json()

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error calling Lens API: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Lens API: {str(e)}")
            raise

    async def _call_patentview_api(self, query: str) -> Dict[str, Any]:
        """Call PatentView API as fallback with normalized output"""
        if not self.session:
            raise RuntimeError("PatentAgent session not initialized. Use as async context manager.")

        # PatentView uses different query syntax
        payload = {
            "q": {
                "text": {
                    "patent_title": query
                }
            },
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", "inventors", "assignees"],
            "o": {"per_page": 50}
        }

        try:
            async with self.session.post(
                self.PATENTVIEW_API_URL,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=f"PatentView API error: {error_text}",
                        headers=response.headers
                    )

                return await response.json()

        except Exception as e:
            logger.warning(f"PatentView API call failed (using Lens only): {str(e)}")
            return {"patents": []}

    def _normalize_lens_patent(self, patent: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Lens API patent response to canonical schema"""
        return {
            "source": "lens",
            "publication_id": f"lens::{patent.get('lens_id', '')}",
            "title": patent.get('title', ''),
            "abstract": patent.get('abstract', ''),
            "filing_date": patent.get('filing_date', ''),
            "grant_date": patent.get('grant_date', ''),
            "inventors": [
                {
                    "name": inventor.get('name', ''),
                    "country": inventor.get('country', '')
                }
                for inventor in patent.get('inventors', [])
            ],
            "assignees": [
                {
                    "name": assignee.get('name', ''),
                    "country": assignee.get('country', '')
                }
                for assignee in patent.get('assignees', [])
            ],
            "jurisdictions": patent.get('jurisdictions', []),
            "citation_count": len(patent.get('citations', [])),
            "relevance_score": 1.0  # Lens doesn't provide relevance score
        }

    def _normalize_patentview_patent(self, patent: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize PatentView API patent response to canonical schema"""
        return {
            "source": "patentview",
            "publication_id": f"patentview::{patent.get('patent_id', '')}",
            "title": patent.get('patent_title', ''),
            "abstract": patent.get('patent_abstract', ''),
            "filing_date": patent.get('application', {}).get('filing_date', ''),
            "grant_date": patent.get('patent_date', ''),
            "inventors": [
                {
                    "name": f"{inv.get('inventor_name_first', '')} {inv.get('inventor_name_last', '')}".strip(),
                    "country": inv.get('inventor_country', '')
                }
                for inv in patent.get('inventors', [])
            ],
            "assignees": [
                {
                    "name": assignee.get('assignee_organization', ''),
                    "country": assignee.get('assignee_country', '')
                }
                for assignee in patent.get('assignees', [])
            ],
            "jurisdictions": ["US"],  # PatentView is US-focused
            "citation_count": patent.get('patent_num_times_cited_by_us_patents', 0),
            "relevance_score": 0.9  # Slightly lower than Lens as fallback
        }

    def _deduplicate_patents(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate patents by publication_id, keeping highest relevance score"""
        seen = {}
        for patent in patents:
            pub_id = patent['publication_id']
            if pub_id not in seen or patent['relevance_score'] > seen[pub_id]['relevance_score']:
                seen[pub_id] = patent
        return list(seen.values())

    async def novelty_check(self, query: str) -> Dict[str, Any]:
        """
        Perform patent novelty check with normalized output schema.
        Returns consistent structure regardless of data source.
        """
        try:
            # Call both APIs concurrently
            lens_task = self._call_lens_api(query)
            patentview_task = self._call_patentview_api(query)

            lens_result, patentview_result = await asyncio.gather(
                lens_task, patentview_task,
                return_exceptions=True
            )

            # Handle API failures gracefully
            patents = []

            # Process Lens results
            if isinstance(lens_result, Exception):
                logger.error(f"Lens API failed: {str(lens_result)}")
            else:
                lens_patents = lens_result.get('data', [])
                patents.extend([self._normalize_lens_patent(p) for p in lens_patents])

            # Process PatentView results (only if Lens failed or has few results)
            if isinstance(patentview_result, Exception):
                logger.warning(f"PatentView API failed: {str(patentview_result)}")
            elif not patents or len(patents) < 10:  # Only use PatentView if Lens has insufficient results
                patentview_patents = patentview_result.get('patents', [])
                patents.extend([self._normalize_patentview_patent(p) for p in patentview_patents])

            # Deduplicate and sort by relevance
            unique_patents = self._deduplicate_patents(patents)
            unique_patents.sort(key=lambda x: x['relevance_score'], reverse=True)

            # Generate summary statistics
            counts = {
                "total_patents": len(unique_patents),
                "lens_patents": sum(1 for p in unique_patents if p['source'] == 'lens'),
                "patentview_patents": sum(1 for p in unique_patents if p['source'] == 'patentview'),
                "jurisdictions": list(set(j for p in unique_patents for j in p.get('jurisdictions', []))),
                "avg_citation_count": (sum(p['citation_count'] for p in unique_patents) / len(unique_patents)) if unique_patents else 0
            }

            return {
                "findings": {
                    "normalized": {
                        "patents": unique_patents,
                        "counts": counts,
                        "query": query,
                        "search_timestamp": asyncio.get_event_loop().time()
                    }
                }
            }

        except Exception as e:
            logger.error(f"Novelty check failed: {str(e)}", exc_info=True)
            # Return empty but valid structure to prevent downstream errors
            return {
                "findings": {
                    "normalized": {
                        "patents": [],
                        "counts": {
                            "total_patents": 0,
                            "lens_patents": 0,
                            "patentview_patents": 0,
                            "jurisdictions": [],
                            "avg_citation_count": 0
                        },
                        "query": query,
                        "search_timestamp": asyncio.get_event_loop().time(),
                        "error": str(e)
                    }
                }
            }
