 feat/robust-token-estimation-13849698795088988745
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

import os
import logging
import asyncio
import aiohttp
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Set, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

@dataclass
class PatentRecord:
    """Canonical patent schema ensuring consistent downstream processing"""
    source: str
    publication_id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    date_published: Optional[str] = None
    assignees: List[str] = None
    classifications: Dict[str, List[str]] = None
    url: Optional[str] = None
    relevance_score: float = 1.0
    raw: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.assignees is None:
            self.assignees = []
        if self.classifications is None:
            self.classifications = {"cpc": [], "ipc": [], "uspc": []}

class PatentAgent:
    """
    Production-ready patent research agent with connection pooling, retries, and canonical output.
    Uses Lens API (primary) + PatentsView (fallback) with proper authentication and deduplication.
    """

    LENS_API_URL = "https://api.lens.org/patent/search"
    PATENTSVIEW_API_URL = "https://search.patentsview.org/api/v1/patent"
    
    def __init__(self, session: aiohttp.ClientSession | None = None):
        self._session = session
        self.lens_token = self._get_lens_token()
        self.connector = aiohttp.TCPConnector(
            limit=20,           # Total connections
            limit_per_host=5,   # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL in seconds
            keepalive_timeout=30
        )
        self.timeout = aiohttp.ClientTimeout(total=45, connect=10, sock_read=30)

    def _get_lens_token(self) -> str:
        """Securely retrieve Lens API token with validation"""
        token = os.getenv('LENS_API_TOKEN')
        if not token:
            raise ValueError("LENS_API_TOKEN environment variable not set")
        if len(token.strip()) < 20:  # Basic validation
            raise ValueError("Invalid LENS_API_TOKEN format - too short")
        return token.strip()

    async def __aenter__(self):
        """Async context manager for connection pooling"""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'RainmakerOrchestrator/1.0',
                    'Content-Type': 'application/json'
                }
            )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Graceful cleanup of connection pool"""
        if self._session:
            await self._session.close()
            self._session = None

    def _canon(self, record: PatentRecord) -> Dict[str, Any]:
        """Convert to canonical dictionary format"""
        return asdict(record)

    def _dedupe(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate patents by source::publication_id with relevance scoring"""
        seen: Dict[str, Dict[str, Any]] = {}
        
        for p in patents:
            pid = p.get("publication_id", "").strip()
            if not pid:
                continue
                
            key = f"{p.get('source', 'unknown')}::{pid}"
            current_score = p.get('relevance_score', 1.0)
            
            # Keep highest relevance score version
            if key not in seen or current_score > seen[key].get('relevance_score', 0):
                seen[key] = p
        
        return list(seen.values())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def search_lens_api(self, query: str, limit: int = 15) -> Dict[str, Any]:
        """Search Lens API with proper authentication and retry logic"""
        if not self._session:
            raise RuntimeError("PatentAgent session not initialized. Use as async context manager.")

        payload = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"title": {"query": query, "boost": 3.0}}},
                        {"match": {"abstract": {"query": query, "boost": 2.0}}},
                        {"match": {"claim": {"query": query, "boost": 1.5}}},
                        {"match": {"description": {"query": query, "boost": 1.0}}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": limit,
            "include": ["biblio", "abstract", "doc_key", "lens_id", "date_published"],
            "sort": [{"date_published": "desc"}]
        }

        try:
            async with self._session.post(
                self.LENS_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.lens_token}",
                    "Content-Type": "application/json"
                }
            ) as resp:
                if resp.status == 401:
                    logger.error("Lens API authentication failed - invalid or expired token")
                    return {
                        "status": "error",
                        "source": "lens",
                        "message": "Authentication failed - check LENS_API_TOKEN validity",
                        "patents": []
                    }
                
                if resp.status >= 400:
                    error_text = await resp.text()
                    logger.error(f"Lens API error {resp.status}: {error_text}")
                    return {
                        "status": "error",
                        "source": "lens",
                        "message": f"HTTP {resp.status}: {error_text[:200]}",
                        "patents": []
                    }

                data = await resp.json()
                rows = data.get("data", [])
                
                patents: List[Dict[str, Any]] = []
                for i, r in enumerate(rows):
                    doc_key = r.get("doc_key") or r.get("lens_id") or f"lens_{i}"
                    biblio = r.get("biblio", {})
                    
                    # Extract title with fallbacks
                    title = None
                    inv_titles = biblio.get("invention_title", [])
                    if isinstance(inv_titles, list) and inv_titles:
                        for title_obj in inv_titles:
                            if isinstance(title_obj, dict) and title_obj.get("text"):
                                title = title_obj["text"]
                                break
                    if not title and biblio.get("title"):
                        title = biblio.get("title")
                    
                    # Extract assignees
                    assignees = []
                    parties = biblio.get("parties", {})
                    applicants = parties.get("applicants", [])
                    
                    if isinstance(applicants, list):
                        for applicant in applicants:
                            if isinstance(applicant, dict):
                                # Try different field names Lens might use
                                for field in ["name", "applicant_name", "organization"]:
                                    if applicant.get(field):
                                        assignees.append(str(applicant[field]))
                                        break
                
                    # Calculate relevance based on position and match quality
                    relevance_score = max(0.5, 1.0 - (i * 0.1))  # Position-based decay
                    
                    patents.append(
                        self._canon(
                            PatentRecord(
                                source="lens",
                                publication_id=str(doc_key),
                                title=title,
                                abstract=(r.get("abstract") or {}).get("text") if isinstance(r.get("abstract"), dict) else (r.get("abstract") or ""),
                                date_published=r.get("date_published"),
                                assignees=assignees,
                                classifications={"cpc": [], "ipc": [], "uspc": []},
                                url=f"https://www.lens.org/lens/patent/{doc_key}",
                                relevance_score=relevance_score,
                                raw=r
                            )
                        )
                    )

                return {
                    "status": "success",
                    "source": "lens",
                    "query": query,
                    "count": len(patents),
                    "patents": patents
                }

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Lens API network error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Lens API call: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "source": "lens",
                "message": f"Unexpected error: {str(e)}",
                "patents": []
            }

    async def search_patentsview_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search PatentsView API as fallback with normalized output"""
        if not self._session:
            raise RuntimeError("PatentAgent session not initialized. Use as async context manager.")

        payload = {
            "q": {
                "text": {
                    "patent_abstract": query
                }
            },
            "f": [
                "patent_id", "patent_title", "patent_abstract", "patent_date",
                "assignees.assignee_organization", "cpc.cpc_class", "ipc.ipc_class"
            ],
            "o": {
                "per_page": limit,
                "matched_subentities_only": "false",
                "sort": [{"patent_date": "desc"}]
            }
        }

        try:
            async with self._session.post(
                self.PATENTSVIEW_API_URL,
                json=payload
            ) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    logger.warning(f"PatentsView API error {resp.status}: {error_text}")
                    return {
                        "status": "error",
                        "source": "patentsview",
                        "message": f"HTTP {resp.status}: {error_text[:200]}",
                        "patents": []
                    }

                data = await resp.json()
                patents_data = data.get("patents", [])
                
                patents: List[Dict[str, Any]] = []
                for i, p in enumerate(patents_data):
                    patent_id = p.get("patent_id", "")
                    if not patent_id:
                        continue
                    
                    # Extract assignees
                    assignees = []
                    for assignee in (p.get("assignees") or []):
                        if isinstance(assignee, dict) and assignee.get("assignee_organization"):
                            assignees.append(assignee["assignee_organization"])
                    
                    # Extract classifications
                    cpc_classes = []
                    for cpc in (p.get("cpc") or []):
                        if isinstance(cpc, dict) and cpc.get("cpc_class"):
                            cpc_classes.append(cpc["cpc_class"])
                    
                    ipc_classes = []
                    for ipc in (p.get("ipc") or []):
                        if isinstance(ipc, dict) and ipc.get("ipc_class"):
                            ipc_classes.append(ipc["ipc_class"])
                    
                    patents.append(
                        self._canon(
                            PatentRecord(
                                source="patentsview",
                                publication_id=f"US{patent_id}",
                                title=p.get("patent_title"),
                                abstract=p.get("patent_abstract"),
                                date_published=p.get("patent_date"),
                                assignees=assignees,
                                classifications={
                                    "cpc": cpc_classes,
                                    "ipc": ipc_classes,
                                    "uspc": []
                                },
                                url=f"https://patents.google.com/patent/US{patent_id}",
                                relevance_score=0.9 - (i * 0.05),  # Slightly lower than Lens
                                raw=p
                            )
                        )
                    )

                return {
                    "status": "success",
                    "source": "patentsview",
                    "query": query,
                    "count": len(patents),
                    "patents": patents
                }

        except Exception as e:
            logger.warning(f"PatentsView API failed (using Lens only): {str(e)}")
            return {
                "status": "error",
                "source": "patentsview",
                "message": str(e),
                "patents": []
            }

    def _extract_terms(self, text: str) -> List[str]:
        """Extract relevant search terms with stopword filtering"""
        stop_words = {"a", "the", "and", "or", "in", "for", "is", "of", "to", "with", "by", "on", "at", "as", "an", "this", "that", "these", "those"}
        # Split by whitespace and punctuation
        words = [word.strip(".,;:()[]{}\"'").lower() for word in text.split()]
        # Filter and deduplicate
        filtered = [w for w in words if len(w) > 3 and w not in stop_words and not w.isdigit()]
        return list(dict.fromkeys(filtered))[:8]  # Deduplicate while preserving order

    async def novelty_check(self, invention_description: str) -> Dict[str, Any]:
        """Perform comprehensive novelty check across multiple sources and terms"""
        key_terms = self._extract_terms(invention_description)
        logger.info(f"Extracted search terms: {key_terms}")

        findings: Dict[str, Any] = {
            "invention": invention_description[:250] + "..." if len(invention_description) > 250 else invention_description,
            "key_terms": key_terms,
            "sources": {},  # Per-term source statistics
            "normalized": {
                "patents": [],
                "counts": {
                    "total_queries": len(key_terms[:3]),
                    "lens_success": 0,
                    "patentsview_success": 0,
                    "terms_searched": key_terms[:3]
                }
            },
            "search_timestamp": asyncio.get_event_loop().time(),
            "execution_time": 0.0
        }

        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run searches for top 3 terms concurrently
            term_tasks = []
            for term in key_terms[:3]:
                term_tasks.append(asyncio.create_task(self._search_term(term)))
            
            results = await asyncio.gather(*term_tasks, return_exceptions=True)
            
            # Process results
            for i, term in enumerate(key_terms[:3]):
                if i < len(results) and not isinstance(results[i], Exception):
                    term_result = results[i]
                    findings["sources"][term] = term_result["sources"]
                    
                    if term_result.get("lens_patents"):
                        findings["normalized"]["patents"].extend(term_result["lens_patents"])
                        findings["normalized"]["counts"]["lens_success"] += 1
                    
                    if term_result.get("pv_patents"):
                        findings["normalized"]["patents"].extend(term_result["pv_patents"])
                        findings["normalized"]["counts"]["patentsview_success"] += 1
                else:
                    error = results[i] if i < len(results) else "No result"
                    logger.error(f"Term '{term}' search failed: {str(error)}")
                    findings["sources"][term] = {
                        "lens": {"status": "error", "message": str(error)},
                        "patentsview": {"status": "error", "message": str(error)}
                    }

            # Deduplicate and sort by relevance
            unique_patents = self._dedupe(findings["normalized"]["patents"])
            unique_patents.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            findings["normalized"]["patents"] = unique_patents[:50]  # Limit to top 50
            findings["normalized"]["counts"]["total_unique"] = len(unique_patents)
            findings["normalized"]["counts"]["total_returned"] = len(findings["normalized"]["patents"])
            
            execution_time = asyncio.get_event_loop().time() - start_time
            findings["execution_time"] = round(execution_time, 2)
            logger.info(f"Novelty check completed in {execution_time:.2f}s with {len(unique_patents)} unique patents")
            
            return {
                "status": "success",
                "task": "novelty_check",
                "findings": findings,
                "recommendation": self._assess_novelty(findings),
                "metadata": {
                    "lens_api_url": self.LENS_API_URL,
                    "total_terms": len(key_terms),
                    "search_terms_used": key_terms[:3]
                }
            }
            
        except Exception as e:
            logger.error(f"Novelty check failed: {str(e)}", exc_info=True)
            execution_time = asyncio.get_event_loop().time() - start_time
            return {
                "status": "error",
                "task": "novelty_check",
                "error": str(e),
                "execution_time": round(execution_time, 2),
                "findings": findings  # Return partial results if available
            }

    async def _search_term(self, term: str) -> Dict[str, Any]:
        """Search a single term across both APIs concurrently"""
        lens_task = self.search_lens_api(term, limit=15)
        pv_task = self.search_patentsview_api(term, limit=10)
        
        lens_result, pv_result = await asyncio.gather(lens_task, pv_task)
        
        return {
            "term": term,
            "sources": {
                "lens": {
                    "status": lens_result.get("status"),
                    "count": lens_result.get("count", 0),
                    "message": lens_result.get("message")
                },
                "patentsview": {
                    "status": pv_result.get("status"),
                    "count": pv_result.get("count", 0),
                    "message": pv_result.get("message")
                }
            },
            "lens_patents": lens_result.get("patents", []) if lens_result.get("status") == "success" else [],
            "pv_patents": pv_result.get("patents", []) if pv_result.get("status") == "success" else []
        }

    def _assess_novelty(self, findings: Dict[str, Any]) -> str:
        """Generate novelty assessment based on patent landscape"""
        counts = findings.get("normalized", {}).get("counts", {})
        total = counts.get("total_unique", 0)
        
        if total == 0:
            return "HIGH novelty potential: No similar patents found in comprehensive search across Lens and USPTO databases"
        elif total <= 3:
            return "MODERATE-HIGH novelty: Very few similar patents identified; strong differentiation likely achievable with proper claim drafting"
        elif total <= 8:
            return "MODERATE novelty: Some similar patents exist; focus on unique aspects and specific embodiments for differentiation"
        elif total <= 15:
            return "MODERATE-LOW novelty: Several similar patents found; requires careful claim construction and emphasis on novel combinations"
        elif total <= 30:
            return "LOW novelty: Dense patent landscape in this area; consider alternative approaches or significant improvements over prior art"
        else:
            return "VERY LOW novelty: Highly saturated field; substantial innovation or completely new approach needed for patentability"
 main
