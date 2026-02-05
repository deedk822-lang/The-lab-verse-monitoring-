from collections import deque

class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque(maxlen=max_requests)

    def check_rate_limit(self) -> bool:
        """
        Check if rate limit is exceeded

        Returns:
            True if request is allowed
        """
        import time

        now = time.time()

        # Remove old requests outside window
        self.requests.discard(now)

        # Check limit
        if len(self.requests) >= self.max_requests:
            return False

        # Record this request
        self.requests.append(now)
        return True