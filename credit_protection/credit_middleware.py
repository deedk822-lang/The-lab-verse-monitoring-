#!/usr/bin/env python3
"""
VAAL AI Empire - Credit Protection Middleware
Real FastAPI middleware that protects LLM API calls
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import re
from typing import Callable
from credit_manager import CreditManager

class CreditProtectionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that protects all LLM API calls
    Automatically estimates token usage and blocks requests that exceed limits
    """
    
    def __init__(self, app, tier: str = "free", data_dir: str = "/tmp/vaal_credits"):
        super().__init__(app)
        self.manager = CreditManager(tier=tier, data_dir=data_dir)
        
        # Patterns to detect LLM API endpoints
        self.llm_patterns = [
            r'/api/v1/kimi',
            r'/api/v1/qwen',
            r'/api/v1/huggingface',
            r'/api/v1/chat',
            r'/api/v1/completion',
            r'/generate',
            r'/chat',
        ]
    
    def _is_llm_request(self, path: str) -> bool:
        """Check if this is an LLM API request"""
        return any(re.search(pattern, path, re.IGNORECASE) for pattern in self.llm_patterns)
    
    def _estimate_tokens_from_request(self, body: dict) -> int:
        """Estimate tokens from request body"""
        # Try to get prompt/messages
        text = ""
        if "prompt" in body:
            text = body["prompt"]
        elif "messages" in body:
            for msg in body["messages"]:
                if isinstance(msg, dict) and "content" in msg:
                    text += msg["content"] + " "
        elif "input" in body:
            text = body["input"]
        elif "text" in body:
            text = body["text"]
        
        # Rough estimation: 1 token ≈ 4 characters
        # Add requested max_tokens if specified
        estimated = len(text) // 4
        if "max_tokens" in body:
            estimated += body["max_tokens"]
        else:
            # Default output size
            estimated += 500
        
        return max(estimated, 100)  # Minimum 100 tokens
    
    def _get_model_from_request(self, body: dict, path: str) -> str:
        """Detect model from request"""
        if "model" in body:
            model_name = body["model"].lower()
            if "kimi" in model_name:
                return "kimi"
            elif "qwen" in model_name:
                return "qwen"
            elif "hugging" in model_name or "hf" in model_name:
                return "huggingface"
        
        # Fallback to path
        if "kimi" in path.lower():
            return "kimi"
        elif "qwen" in path.lower():
            return "qwen"
        elif "huggingface" in path.lower():
            return "huggingface"
        
        return "kimi"  # Default
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercept all requests"""
        # Only check LLM requests
        if not self._is_llm_request(request.url.path):
            return await call_next(request)
        
        # Check circuit breaker first
        breaker_active, breaker_reason = self.manager.check_circuit_breaker()
        if breaker_active:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Circuit breaker active",
                    "message": breaker_reason,
                    "retry_after": 3600  # 1 hour
                }
            )
        
        # Get request body
        try:
            body = await request.json()
        except:
            body = {}
        
        # Estimate tokens and model
        estimated_tokens = self._estimate_tokens_from_request(body)
        model = self._get_model_from_request(body, request.url.path)
        
        # Check if request is allowed
        allowed, reason, usage_info = self.manager.can_make_request(estimated_tokens, model)
        
        if not allowed:
            # Calculate percentage for user
            daily_pct = (usage_info.get("cost", 0) / self.manager.config["daily_max_cost"]) * 100
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Credit limit reached",
                    "message": reason,
                    "tier": self.manager.tier,
                    "daily_usage_percent": round(daily_pct, 1),
                    "daily_usage": {
                        "requests": usage_info.get("requests", 0),
                        "max_requests": self.manager.config["daily_max_requests"],
                        "cost": f"${usage_info.get('cost', 0):.4f}",
                        "max_cost": f"${self.manager.config['daily_max_cost']:.2f}"
                    }
                }
            )
        
        # Allow request and time it
        start_time = time.time()
        response = await call_next(request)
        elapsed_time = time.time() - start_time
        
        # Record actual usage (use estimated for now, ideally parse response)
        # In production, you'd parse the actual token count from the LLM response
        self.manager.record_usage(estimated_tokens, model)
        
        # Add usage headers to response
        summary = self.manager.get_usage_summary()
        response.headers["X-Credit-Tier"] = self.manager.tier
        response.headers["X-Daily-Requests"] = f"{summary['daily']['usage']['requests']}/{summary['daily']['limits']['requests']}"
        response.headers["X-Daily-Cost"] = f"${summary['daily']['usage']['cost']:.4f}/${summary['daily']['limits']['cost']:.2f}"
        response.headers["X-Daily-Usage-Percent"] = f"{summary['daily']['percentages']['cost']:.1f}%"
        response.headers["X-Request-Time"] = f"{elapsed_time:.2f}s"
        
        return response

def protect_function(tier: str = "free", data_dir: str = "/tmp/vaal_credits"):
    """
    Decorator to protect individual functions
    
    Usage:
        @protect_function(tier="free")
        def my_llm_function(prompt: str):
            # Call LLM API
            return result
    """
    manager = CreditManager(tier=tier, data_dir=data_dir)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Estimate tokens from arguments
            prompt = ""
            if args:
                prompt = str(args[0])
            elif "prompt" in kwargs:
                prompt = kwargs["prompt"]
            elif "text" in kwargs:
                prompt = kwargs["text"]
            
            estimated_tokens = len(prompt) // 4 + 500
            
            # Check if allowed
            allowed, reason, _ = manager.can_make_request(estimated_tokens)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Credit limit reached: {reason}"
                )
            
            # Call function
            result = func(*args, **kwargs)
            
            # Record usage
            manager.record_usage(estimated_tokens)
            
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the decorator
    print("Testing protection decorator...")
    
    @protect_function(tier="free")
    def call_llm(prompt: str):
        print(f"LLM called with: {prompt[:50]}...")
        return {"response": "Test response", "tokens": 500}
    
    # Test 1: Normal call
    print("\n=== Test 1: Normal call ===")
    try:
        result = call_llm("What is the weather today?")
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Simulate many calls
    print("\n=== Test 2: Simulate many calls ===")
    for i in range(50):
        try:
            result = call_llm(f"Test prompt {i}" * 100)  # Long prompt
        except HTTPException as e:
            print(f"Blocked at request {i}: {e.detail}")
            break
    
    # Test 3: Check usage
    print("\n=== Test 3: Check usage ===")
    from credit_manager import CreditManager
    manager = CreditManager(tier="free")
    summary = manager.get_usage_summary()
    print(f"Total requests: {summary['daily']['usage']['requests']}")
    print(f"Total cost: ${summary['daily']['usage']['cost']:.4f}")
    print(f"Usage: {summary['daily']['percentages']['cost']:.1f}%")
