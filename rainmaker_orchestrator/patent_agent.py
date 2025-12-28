# rainmaker_orchestrator/patent_agent.py

import os
import aiohttp
 feat/refactor-patent-agent-7332476735558934785
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Set


@dataclass
class PatentRecord:
    source: str
    publication_id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    date_published: Optional[str] = None
    assignees: List[str] = None
    classifications: Dict[str, List[str]] = None
    url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


import json
from typing import Dict, List, Any
import os
 main

class PatentAgent:
    """
    Patent research agent using open APIs + permitted sources.
    Normalizes results into a canonical schema.
    """

    def __init__(self, session: aiohttp.ClientSession | None = None):
        self.patentsview_url = "https://www.patentsview.org/api/patents/query"
 feat/refactor-patent-agent-7332476735558934785
        self.lens_api_url = "https://api.lens.org/patent/search"  # correct endpoint [web:145][web:151]
        self._session = session

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=45)
            )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _canon(self, record: PatentRecord) -> Dict[str, Any]:
        if record.assignees is None:
            record.assignees = []
        if record.classifications is None:
            record.classifications = {"cpc": [], "ipc": [], "uspc": []}
        return asdict(record)

    async def search_patentsview_api(self, query: str, limit: int = 10) -> Dict[str, Any]:

        self.lens_api_url = "https://api.lens.org/patent/search"

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

 main
        payload = {
            "q": {"patent_abstract": {"text": query}},
            "f": [
                "patent_id", "patent_title", "patent_abstract", "patent_date",
                "assignee_name", "ipc_classification", "uspc_classification"
            ],
            "size": limit,
            "sort": [{"patent_date": "desc"}]
        }

        assert self._session is not None, "Use PatentAgent as an async context manager"

        async with self._session.post(self.patentsview_url, json=payload) as resp:
            if resp.status != 200:
                return {"status": "error", "source": "patentsview", "message": f"HTTP {resp.status}", "patents": []}

            data = await resp.json()
            patents = []
            for p in data.get("patents", []):
                pid = p.get("patent_id")
                patents.append(self._canon(PatentRecord(
                    source="patentsview",
                    publication_id=str(pid) if pid else "",
                    title=p.get("patent_title"),
                    abstract=p.get("patent_abstract"),
                    date_published=p.get("patent_date"),
                    assignees=[
                        a.get("assignee_name")
                        for a in (p.get("assignee_name") or [])
                        if isinstance(a, dict) and a.get("assignee_name")
                    ] if isinstance(p.get("assignee_name"), list) else ([] if not p.get("assignee_name") else [p.get("assignee_name")]),
                    classifications={
                        "cpc": [],
                        "ipc": [
                            c.get("ipc_classification")
                            for c in (p.get("ipc_classification") or [])
                            if isinstance(c, dict) and c.get("ipc_classification")
                        ],
                        "uspc": [
                            c.get("uspc_classification")
                            for c in (p.get("uspc_classification") or [])
                            if isinstance(c, dict) and c.get("uspc_classification")
                        ]
                    },
                    url=f"https://patents.google.com/patent/US{pid}" if pid else None,
                    raw=p
                )))

            return {"status": "success", "source": "patentsview", "query": query, "count": len(patents), "patents": patents}

    async def search_lens_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        token = os.getenv("LENS_API_TOKEN")
        if not token:
            return {"status": "error", "source": "lens", "message": "Missing LENS_API_TOKEN", "patents": []}

        payload = {
            "query": {"text": query},
            "size": limit,
            "include": ["biblio", "doc_key"]  # per Lens examples [web:145]
        }

 feat/refactor-patent-agent-7332476735558934785
        assert self._session is not None, "Use PatentAgent as an async context manager"

        async with self._session.post(
            self.lens_api_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"  # required [web:145][web:151]

        try:
            token = os.getenv("LENS_API_TOKEN")  # store as secret env var
            if not token:
                return {"status": "error", "message": "Missing LENS_API_TOKEN"}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.lens_api_url}",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}"
                    }
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
 main
            }
        ) as resp:
            if resp.status != 200:
                return {"status": "error", "source": "lens", "message": f"HTTP {resp.status}", "patents": []}

            data = await resp.json()

            # Lens response shapes vary by include-fields; normalize defensively.
            rows = data.get("data") or data.get("results") or []
            patents = []
            for r in rows:
                biblio = r.get("biblio", {}) if isinstance(r, dict) else {}
                doc_key = r.get("doc_key") or r.get("lens_id") or r.get("publication_number") or ""

                title = None
                if isinstance(biblio.get("title"), list) and biblio["title"]:
                    title = biblio["title"][0].get("text")
                elif isinstance(biblio.get("title"), str):
                    title = biblio.get("title")

                patents.append(self._canon(PatentRecord(
                    source="lens",
                    publication_id=str(doc_key),
                    title=title,
                    abstract=None,
                    date_published=r.get("date_published") or r.get("publication_date"),
                    assignees=[
                        a.get("name")
                        for a in (biblio.get("applicants") or [])
                        if isinstance(a, dict) and a.get("name")
                    ],
                    classifications={"cpc": [], "ipc": [], "uspc": []},
                    url=None,
                    raw=r
                )))

            return {"status": "success", "source": "lens", "query": query, "count": len(patents), "patents": patents}

    def _extract_terms(self, text: str) -> List[str]:
        stop_words = {"a", "the", "and", "or", "in", "for", "is", "of"}
        words = text.lower().split()
        return [w for w in words if len(w) > 4 and w not in stop_words]

    def _dedupe(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Set[str] = set()
        out = []
        for p in patents:
            key = f"{p.get('source')}::{p.get('publication_id')}"
            if key not in seen and p.get("publication_id"):
                seen.add(key)
                out.append(p)
        return out

    async def novelty_check(self, invention_description: str) -> Dict[str, Any]:
        key_terms = self._extract_terms(invention_description)

        findings = {
            "invention": invention_description[:200],
            "key_terms": key_terms[:12],
            "sources": {},
            "normalized": {
                "patents": [],
                "counts": {}
            }
        }

        # Search top terms (keep your current behavior but don't overwrite results)
        for term in key_terms[:3]:
            pv = await self.search_patentsview_api(term, limit=10)
            ln = await self.search_lens_api(term, limit=10)

            if pv.get("status") == "success":
                findings["normalized"]["patents"].extend(pv.get("patents", []))
            if ln.get("status") == "success":
                findings["normalized"]["patents"].extend(ln.get("patents", []))

            findings["sources"][term] = {
                "patentsview": {"status": pv.get("status"), "count": pv.get("count", 0)},
                "lens": {"status": ln.get("status"), "count": ln.get("count", 0)}
            }

        findings["normalized"]["patents"] = self._dedupe(findings["normalized"]["patents"])
        findings["normalized"]["counts"] = {
            "total_unique": len(findings["normalized"]["patents"])
        }

        return {
            "status": "success",
            "task": "novelty_check",
            "findings": findings,
            "recommendation": self._assess_novelty(findings)
        }

    def _assess_novelty(self, findings: Dict[str, Any]) -> str:
        total_similar = findings.get("normalized", {}).get("counts", {}).get("total_unique", 0)
        if total_similar == 0:
            return "HIGH novelty: No similar patents found in USPTO/Lens databases"
        if total_similar < 5:
            return "MODERATE novelty: Few similar patents; differentiation likely possible"
        if total_similar < 20:
            return "LOW novelty: Multiple similar patents exist; careful claim drafting needed"
        return "VERY LOW novelty: Patent landscape saturated; consider alternative approaches"
