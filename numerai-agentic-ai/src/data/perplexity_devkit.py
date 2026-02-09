from perplexity import Perplexity
from typing import List, Dict, Literal, Optional, Union
import json
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerplexityNumeraiDevKit:
    """
    Production fetcher for Numerai + Phase 2 improvements using Perplexity Agentic Research API:
    - Unified 'responses.create' endpoint
    - Batch queries via sequential tool calls (Agentic behavior)
    - SEC filing access via web_search tool and specific instructions
    - Structured JSON output via instructions and response parsing
    """
    
    def __init__(self, api_key: str):
        self.client = Perplexity(api_key=api_key)
        self.request_count = 0
        self.start_time = datetime.now()
        
        # Phase 2: Monitoring hooks
        self.perf_metrics = {
            "total_requests": 0,
            "total_tokens": 0,
            "avg_latency_ms": [],
            "errors": []
        }
    
    # ============ NEWS FETCHING (Agentic) ============
    
    def batch_market_news(self, queries: List[str], max_results: int = 5) -> Dict:
        """
        Batch fetch market news using the Agentic Research API.
        
        Args:
            queries: Up to 5 queries (e.g., "AAPL earnings", "MSFT AI")
            max_results: Results per query (handled via instructions)
        
        Returns:
            {query: [{headline, url, summary, source, sentiment}, ...]}
        """
        
        if len(queries) > 5:
            logger.warning(f"Max 5 queries. Splitting {len(queries)} queries.")
            queries = queries[:5]
            
        results = {}
        
        for query in queries:
            try:
                start = datetime.now()
                
                # Agentic Research API call
                instructions = (
                    "You are a financial news analyst. Use the web_search tool to find the latest market news. "
                    "Focus ONLY on trusted financial domains like cnbc.com, bloomberg.com, reuters.com, marketwatch.com. "
                    f"Provide {max_results} distinct news items. "
                    "Format the output as a JSON list of objects with keys: headline, url, summary, source, sentiment (float -1 to 1)."
                )
                
                response = self.client.responses.create(
                    model="sonar-pro", 
                    input=query,
                    tools=[{"type": "web_search"}],
                    instructions=instructions
                )
                
                parsed_data = self._parse_agentic_response(response.output_text)
                results[query] = parsed_data
                
                latency = (datetime.now() - start).total_seconds() * 1000
                self._record_metric(1, latency, "news_agentic")
                
            except Exception as e:
                logger.error(f"News fetch error for {query}: {e}")
                self.perf_metrics["errors"].append({
                    "type": "news_agentic",
                    "query": query,
                    "message": str(e)
                })
                results[query] = []
                
        return results
    
    # ============ SEC FILINGS (Agentic) ============
    
    def fetch_sec_filings(self, ticker: str, filing_type: Literal["10-K", "10-Q", "8-K"] = "10-K") -> Dict:
        """
        Fetch SEC filings using Agentic Research API with specific SEC instructions
        """
        
        query = f"Find the latest {filing_type} filing for {ticker} from 2025 or 2026."
        instructions = (
            "You are an SEC filing researcher. Use web_search to find the specific filing on sec.gov or credible financial sites. "
            "Extract the following fields and return as a JSON object: "
            "filing_type, company, filed_date, url, and a brief snippet/summary of key financial results."
        )
        
        try:
            start = datetime.now()
            
            response = self.client.responses.create(
                model="sonar-reasoning-pro",
                input=query,
                tools=[{"type": "web_search"}],
                instructions=instructions
            )
            
            filing_data = self._parse_agentic_response(response.output_text)
            if isinstance(filing_data, dict):
                filing_data["ticker"] = ticker
            
            latency = (datetime.now() - start).total_seconds() * 1000
            self._record_metric(1, latency, "sec_filing_agentic")
            
            return filing_data if isinstance(filing_data, dict) else {}
            
        except Exception as e:
            logger.error(f"SEC filing error: {e}")
            self.perf_metrics["errors"].append({
                "type": "sec_filing_agentic",
                "ticker": ticker,
                "message": str(e)
            })
            return {}
    
    # ============ FINANCIAL DATA (Agentic Extraction) ============
    
    def extract_financial_metrics(self, company_name: str) -> Dict:
        """
        Extract structured financial metrics using Agentic API
        """
        
        query = f"Get current financial metrics for {company_name}."
        instructions = (
            "You are a quantitative analyst. Use web_search to find current financial data. "
            "Return ONLY a valid JSON object with the following keys: "
            "company, pe_ratio, price_to_book, dividend_yield, 52week_high, 52week_low, "
            "market_cap_billions, revenue_growth_yoy, earnings_per_share, data_quality (0-1 score). "
            "Do not include any markdown formatting like ```json."
        )
        
        try:
            start = datetime.now()
            
            response = self.client.responses.create(
                model="sonar-pro",
                input=query,
                tools=[{"type": "web_search"}],
                instructions=instructions
            )
            
            metrics = self._parse_agentic_response(response.output_text)
            
            latency = (datetime.now() - start).total_seconds() * 1000
            self._record_metric(1, latency, "extraction_agentic")
            
            return metrics if isinstance(metrics, dict) else {}
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return {}
    
    # ============ HELPER METHODS ============
    
    def _parse_agentic_response(self, text: str) -> Union[Dict, List]:
        """Attempt to parse JSON from the response text"""
        try:
            # Clean up potential markdown formatting
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from response: {text[:100]}...")
            return {"error": "parse_error", "raw_text": text}

    def _record_metric(self, requests: int, latency_ms: float, operation: str):
        """Record performance metric"""
        self.perf_metrics["total_requests"] += requests
        self.perf_metrics["avg_latency_ms"].append(latency_ms)
        logger.info(f"[{operation}] Requests: {requests}, Latency: {latency_ms:.1f}ms")
    
    def get_health_metrics(self) -> Dict:
        """Return performance dashboard"""
        avg_latency = (
            sum(self.perf_metrics["avg_latency_ms"]) / 
            len(self.perf_metrics["avg_latency_ms"])
            if self.perf_metrics["avg_latency_ms"] else 0
        )
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        return {
            "total_requests": self.perf_metrics["total_requests"],
            "avg_latency_ms": avg_latency,
            "error_count": len(self.perf_metrics["errors"]),
            "uptime_hours": uptime,
            "recent_errors": self.perf_metrics["errors"][-5:]
        }
