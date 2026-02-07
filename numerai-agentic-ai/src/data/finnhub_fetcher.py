import finnhub
import logging
import time
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FinnhubDataFetcher:
    """
    Finnhub fetcher for Numerai Phase 1.
    Respects free tier limits: 60 requests/minute.
    """
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Finnhub API key is required")
        self.client = finnhub.Client(api_key=api_key)
        self.request_count = 0
        self.last_reset = time.time()
        
    def _rate_limit(self):
        """Simple token bucket rate limiter for 60 req/min"""
        current_time = time.time()
        if current_time - self.last_reset > 60:
            self.request_count = 0
            self.last_reset = current_time
        
        if self.request_count >= 58: # buffer
            sleep_time = 60 - (current_time - self.last_reset) + 1
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_reset = time.time()
        
        self.request_count += 1

    def get_financial_metrics(self, ticker: str) -> Dict:
        """Fetch basic financials"""
        self._rate_limit()
        try:
            return self.client.company_basic_financials(ticker, 'all')
        except Exception as e:
            logger.error(f"Finnhub financials error for {ticker}: {e}")
            return {}

    def get_quote(self, ticker: str) -> Dict:
        """Fetch real-time quote"""
        self._rate_limit()
        try:
            return self.client.quote(ticker)
        except Exception as e:
            logger.error(f"Finnhub quote error for {ticker}: {e}")
            return {}
            
    def batch_fetch_fundamentals(self, tickers: List[str]) -> Dict[str, Dict]:
        """Fetch fundamentals for multiple tickers"""
        results = {}
        for ticker in tickers:
            results[ticker] = self.get_financial_metrics(ticker)
        return results
