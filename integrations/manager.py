"""
Lab-Verse Integration Manager
Unified framework for all platform integrations
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx
from redis import asyncio as aioredis
import json

logger = logging.getLogger(__name__)


@dataclass
class IntegrationHealth:
    """Health status for an integration"""
    platform: str
    status: str  # "healthy", "degraded", "unhealthy"
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    response_time_ms: Optional[float]


class CircuitBreaker:
    """Circuit breaker for resilient API calls"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == "open":
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).seconds
                if time_since_failure > self.timeout:
                    self.state = "half-open"
                    logger.info(f"Circuit breaker entering half-open state")
                    return False
            return True
        return False

    def record_success(self):
        """Record successful call"""
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed call"""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()

        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker opened after {self.failures} failures")


class BasePlatformConnector:
    """Base class for all platform connectors"""

    def __init__(
        self,
        platform_name: str,
        base_url: str,
        api_key: str,
        redis_client: aioredis.Redis,
        cache_ttl: int = 300
    ):
        self.platform_name = platform_name
        self.base_url = base_url
        self.api_key = api_key
        self.redis = redis_client
        self.cache_ttl = cache_ttl
        self.circuit_breaker = CircuitBreaker()

        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=self._get_headers()
        )

        self.health = IntegrationHealth(
            platform=platform_name,
            status="unknown",
            last_success=None,
            last_failure=None,
            consecutive_failures=0,
            response_time_ms=None
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for API calls"""
        return {
            "Content-Type": "application/json",
            "User-Agent": "Lab-Verse-Integration/2.0"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make API request with error handling and retry logic"""

        if self.circuit_breaker.is_open():
            logger.warning(f"{self.platform_name}: Circuit breaker is open, skipping request")
            return None

        url = f"{self.base_url}{endpoint}"
        retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff

        for attempt, delay in enumerate(retry_delays, 1):
            try:
                start_time = datetime.utcnow()

                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()

                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Update health metrics
                self.health.status = "healthy"
                self.health.last_success = datetime.utcnow()
                self.health.consecutive_failures = 0
                self.health.response_time_ms = response_time
                self.circuit_breaker.record_success()

                logger.info(
                    f"{self.platform_name}: {method} {endpoint} "
                    f"succeeded in {response_time:.2f}ms"
                )

                return response.json() if response.text else {}

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"{self.platform_name}: HTTP {e.response.status_code} "
                    f"on {method} {endpoint}"
                )

                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    self._record_failure()
                    return None

            except httpx.RequestError as e:
                logger.error(
                    f"{self.platform_name}: Request error on {method} {endpoint}: {e}"
                )

            except Exception as e:
                logger.error(
                    f"{self.platform_name}: Unexpected error on {method} {endpoint}: {e}"
                )

            # Record failure and retry
            self._record_failure()

            if attempt < len(retry_delays):
                logger.info(
                    f"{self.platform_name}: Retrying in {delay}s "
                    f"(attempt {attempt + 1}/{len(retry_delays)})"
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(f"{self.platform_name}: All retry attempts exhausted for {method} {endpoint}")
        return None

    def _record_failure(self):
        """Record a failed request"""
        self.health.last_failure = datetime.utcnow()
        self.health.consecutive_failures += 1

        if self.health.consecutive_failures >= 3:
            self.health.status = "degraded"
        if self.health.consecutive_failures >= 5:
            self.health.status = "unhealthy"

        self.circuit_breaker.record_failure()

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            cached = await self.redis.get(f"{self.platform_name}:{key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"{self.platform_name}: Cache read error: {e}")
        return None

    async def _set_cache(self, key: str, data: Any, ttl: Optional[int] = None):
        """Set cached data"""
        try:
            ttl = ttl or self.cache_ttl
            await self.redis.setex(
                f"{self.platform_name}:{key}",
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"{self.platform_name}: Cache write error: {e}")

    async def health_check(self) -> IntegrationHealth:
        """Perform health check"""
        return self.health

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class IntegrationManager:
    """Central manager for all platform integrations"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.connectors: Dict[str, BasePlatformConnector] = {}
        self.redis = None

    async def initialize(self):
        """Initialize the integration manager"""
        logger.info("Initializing Integration Manager")

        # Connect to Redis
        self.redis = await aioredis.from_url(
            self.redis_url,
            decode_responses=True
        )

        logger.info("Integration Manager initialized successfully")

    def register_connector(
        self,
        platform_name: str,
        connector: BasePlatformConnector
    ):
        """Register a platform connector"""
        self.connectors[platform_name] = connector
        logger.info(f"Registered connector: {platform_name}")

    def get_connector(self, platform_name: str) -> Optional[BasePlatformConnector]:
        """Get a registered connector"""
        return self.connectors.get(platform_name)

    async def health_check_all(self) -> Dict[str, IntegrationHealth]:
        """Check health of all integrations"""
        health_results = {}

        for platform_name, connector in self.connectors.items():
            try:
                health = await connector.health_check()
                health_results[platform_name] = health
            except Exception as e:
                logger.error(f"Health check failed for {platform_name}: {e}")
                health_results[platform_name] = IntegrationHealth(
                    platform=platform_name,
                    status="unhealthy",
                    last_success=None,
                    last_failure=datetime.utcnow(),
                    consecutive_failures=999,
                    response_time_ms=None
                )

        return health_results

    async def sync_all(self) -> Dict[str, Any]:
        """Trigger sync for all platforms"""
        sync_results = {}

        tasks = []
        for platform_name, connector in self.connectors.items():
            if hasattr(connector, 'sync'):
                tasks.append(self._sync_platform(platform_name, connector))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for platform_name, result in zip(self.connectors.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Sync failed for {platform_name}: {result}")
                sync_results[platform_name] = {"status": "error", "error": str(result)}
            else:
                sync_results[platform_name] = result

        return sync_results

    async def _sync_platform(
        self,
        platform_name: str,
        connector: BasePlatformConnector
    ) -> Dict[str, Any]:
        """Sync a single platform"""
        try:
            logger.info(f"Starting sync for {platform_name}")
            result = await connector.sync()
            logger.info(f"Sync completed for {platform_name}")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Sync error for {platform_name}: {e}")
            return {"status": "error", "error": str(e)}

    async def close_all(self):
        """Close all connections"""
        logger.info("Closing all integration connections")

        for connector in self.connectors.values():
            try:
                await connector.close()
            except Exception as e:
                logger.error(f"Error closing connector: {e}")

        if self.redis:
            await self.redis.close()

        logger.info("All connections closed")


class WebhookValidator:
    """Validate incoming webhooks from various platforms"""

    @staticmethod
    def validate_hubspot(body: bytes, signature: str, secret: str) -> bool:
        """Validate HubSpot webhook signature"""
        import hmac
        import hashlib

        # HubSpot uses SHA-256 HMAC
        expected_signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def validate_clickup(signature: str, secret: str, timestamp: str, body: str) -> bool:
        """Validate ClickUp webhook signature"""
        import hmac
        import hashlib

        # ClickUp signature format
        message = f"{timestamp}.{body}"
        expected_signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def validate_grafana(payload: Dict[str, Any], token: str) -> bool:
        """Validate Grafana webhook token"""
        # Grafana uses simple token validation
        return payload.get("token") == token


# Singleton instance
_integration_manager: Optional[IntegrationManager] = None


async def get_integration_manager(redis_url: str) -> IntegrationManager:
    """Get or create the integration manager singleton"""
    global _integration_manager

    if _integration_manager is None:
        _integration_manager = IntegrationManager(redis_url)
        await _integration_manager.initialize()

    return _integration_manager