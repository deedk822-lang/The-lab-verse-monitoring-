"""
Credit Protection Middleware for FastAPI
Intercepts all LLM requests and enforces quota limits.
"""

import time
import logging
from typing import Callable
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from vaal_ai_empire.credit_protection.manager import (
    get_manager,
    ProviderType,
    ResourceMonitor,
)

logger = logging.getLogger(__name__)


class CreditProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce credit protection on all LLM requests.
    """
    
    def __init__(self, app, enable_resource_monitoring: bool = True):
        super().__init__(app)
        self.credit_manager = get_manager()
        self.resource_monitor = ResourceMonitor(self.credit_manager.quota)
        self.enable_resource_monitoring = enable_resource_monitoring
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with credit protection."""
        
        # Skip non-LLM endpoints
        if not self._is_llm_endpoint(request):
            return await call_next(request)
        
        # Check resource health
        if self.enable_resource_monitoring:
            healthy, message = self.resource_monitor.check_resources()
            if not healthy:
                logger.error(f"Resource limit exceeded: {message}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Service temporarily unavailable",
                        "reason": "Instance resource limits exceeded",
                        "details": message,
                        "retry_after": 300
                    }
                )
        
        # Estimate request cost
        try:
            estimated_tokens, estimated_cost = await self._estimate_request_cost(request)
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            estimated_tokens, estimated_cost = 4000, 0.05
        
        # Check quota
        allowed, reason = self.credit_manager.check_quota(
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost
        )
        
        if not allowed:
            logger.warning(f"Request blocked: {reason}")
            
            usage_summary = self.credit_manager.get_usage_summary()
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Credit limit exceeded",
                    "reason": reason,
                    "usage": usage_summary,
                    "retry_after": self._get_retry_after(reason)
                },
                headers={
                    "Retry-After": str(self._get_retry_after(reason)),
                    "X-RateLimit-Limit": str(self.credit_manager.quota.daily_requests),
                    "X-RateLimit-Remaining": str(
                        max(0, self.credit_manager.quota.daily_requests - 
                        usage_summary["daily"]["requests"])
                    ),
                    "X-RateLimit-Reset": self._get_reset_time()
                }
            )
        
        # Process request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)
            
            actual_tokens, actual_cost = await self._extract_actual_usage(
                response, estimated_tokens, estimated_cost
            )
            
            provider = self._get_provider_type(request)
            self.credit_manager.record_usage(
                provider=provider,
                request_tokens=actual_tokens // 2,
                response_tokens=actual_tokens // 2,
                cost=actual_cost,
                duration_ms=duration_ms,
                status="success",
                metadata={
                    "endpoint": request.url.path,
                    "method": request.method
                }
            )
            
            usage_summary = self.credit_manager.get_usage_summary()
            response.headers["X-Daily-Requests-Used"] = str(usage_summary["daily"]["requests"])
            response.headers["X-Daily-Tokens-Used"] = str(usage_summary["daily"]["tokens"])
            response.headers["X-Daily-Cost-Used"] = f"${usage_summary['daily']['cost_usd']:.4f}"
            
            return response
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            provider = self._get_provider_type(request)
            self.credit_manager.record_usage(
                provider=provider,
                request_tokens=estimated_tokens,
                response_tokens=0,
                cost=estimated_cost,
                duration_ms=duration_ms,
                status="error",
                metadata={
                    "endpoint": request.url.path,
                    "error": str(e)
                }
            )
            
            raise
    
    def _is_llm_endpoint(self, request: Request) -> bool:
        """Check if endpoint is an LLM request."""
        llm_paths = [
            "/api/generate",
            "/api/chat",
            "/api/complete",
            "/v1/completions",
            "/v1/chat/completions"
        ]
        return any(request.url.path.startswith(path) for path in llm_paths)
    
    async def _estimate_request_cost(self, request: Request) -> tuple:
        """Estimate request token count and cost."""
        try:
            body = await request.body()
            estimated_tokens = len(body) // 4
            estimated_tokens += self.credit_manager.quota.max_response_tokens
            estimated_cost = (estimated_tokens / 1000) * 0.01
            return estimated_tokens, estimated_cost
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            return 4000, 0.05
    
    async def _extract_actual_usage(self, response: Response, estimated_tokens: int, estimated_cost: float) -> tuple:
        """Extract actual usage from response."""
        if "X-Tokens-Used" in response.headers:
            try:
                actual_tokens = int(response.headers["X-Tokens-Used"])
                actual_cost = (actual_tokens / 1000) * 0.01
                return actual_tokens, actual_cost
            except (ValueError, TypeError):
                pass
        return estimated_tokens, estimated_cost
    
    def _get_provider_type(self, request: Request) -> ProviderType:
        """Determine provider type from request."""
        path = request.url.path.lower()
        if "kimi" in path:
            return ProviderType.KIMI
        elif "huggingface" in path or "hf" in path:
            return ProviderType.HUGGINGFACE
        elif "qwen" in path:
            return ProviderType.QWEN
        elif "openai" in path:
            return ProviderType.OPENAI
        else:
            return ProviderType.ALIBABA_CLOUD
    
    def _get_retry_after(self, reason: str) -> int:
        """Get retry-after seconds based on reason."""
        if "daily" in reason.lower():
            now = datetime.now()
            tomorrow = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
            return int((tomorrow - now).total_seconds())
        elif "hourly" in reason.lower():
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            return int((next_hour - now).total_seconds())
        else:
            return 300
    
    def _get_reset_time(self) -> str:
        """Get timestamp when limits reset."""
        now = datetime.now()
        tomorrow = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
        return tomorrow.isoformat()
