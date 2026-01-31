"""
Credit Protection Manager for Alibaba Cloud + Kimi CLI + HuggingFace
Prevents runaway costs on free tier instances with multi-layer safeguards.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class TierLevel(Enum):
    """Cost tier levels."""

    FREE = "free"
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"


class ProviderType(Enum):
    """Provider types for tracking."""

    KIMI = "kimi"
    HUGGINGFACE = "huggingface"
    QWEN = "qwen"
    ALIBABA_CLOUD = "alibaba_cloud"
    OPENAI = "openai"


@dataclass
class UsageQuota:
    """Usage quota configuration."""

    # Daily limits
    daily_requests: int = 100
    daily_tokens: int = 50000
    daily_cost_usd: float = 0.50

    # Hourly limits (burst protection)
    hourly_requests: int = 20
    hourly_tokens: int = 10000
    hourly_cost_usd: float = 0.10

    # Per-request limits
    max_request_tokens: int = 4000
    max_response_tokens: int = 2000
    max_request_cost_usd: float = 0.05

    # Instance limits (for Alibaba Cloud)
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    max_disk_percent: float = 90.0


@dataclass
class UsageRecord:
    """Usage tracking record."""

    timestamp: str
    provider: str
    request_tokens: int
    response_tokens: int
    total_tokens: int
    estimated_cost: float
    duration_ms: int
    status: str
    metadata: Dict


class CreditProtectionManager:
    """
    Comprehensive credit protection manager.

    Features:
    - Multi-provider quota tracking
    - Real-time usage monitoring
    - Automatic circuit breakers
    - Graceful degradation
    - Alert mechanisms
    """

    def __init__(
        self, quota: UsageQuota, storage_path: str = "/var/lib/vaal/credit_protection", tier: TierLevel = TierLevel.FREE
    ):
        self.quota = quota
        self.storage_path = Path(storage_path)
        self.tier = tier
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Usage tracking
        self.daily_usage: Dict[str, int] = {}
        self.hourly_usage: Dict[str, int] = {}
        self.request_count = 0

        # Circuit breaker state
        self.circuit_open = False
        self.circuit_open_until: Optional[datetime] = None

        # Load existing usage data
        self._load_usage()

    def _get_usage_file(self, period: str = "daily") -> Path:
        """Get usage file path for period."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.storage_path / f"usage_{period}_{today}.json"

    def _load_usage(self):
        """Load existing usage data."""
        daily_file = self._get_usage_file("daily")
        hourly_file = self._get_usage_file("hourly")

        try:
            if daily_file.exists():
                with open(daily_file) as f:
                    self.daily_usage = json.load(f)

            if hourly_file.exists():
                with open(hourly_file) as f:
                    self.hourly_usage = json.load(f)
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")

    def _save_usage(self):
        """Save current usage data."""
        daily_file = self._get_usage_file("daily")
        hourly_file = self._get_usage_file("hourly")

        try:
            with open(daily_file, "w") as f:
                json.dump(self.daily_usage, f)

            with open(hourly_file, "w") as f:
                json.dump(self.hourly_usage, f)
        except Exception as e:
            logger.error(f"Error saving usage data: {e}")

    def _get_current_usage(self, period: str = "daily") -> Dict:
        """Get current usage statistics."""
        usage = self.daily_usage if period == "daily" else self.hourly_usage

        return {
            "requests": usage.get("requests", 0),
            "tokens": usage.get("tokens", 0),
            "cost_usd": usage.get("cost_usd", 0.0),
            "timestamp": usage.get("last_update", datetime.now().isoformat()),
        }

    def _update_usage(self, tokens: int, cost: float, period: str = "daily"):
        """Update usage statistics."""
        usage = self.daily_usage if period == "daily" else self.hourly_usage

        usage["requests"] = usage.get("requests", 0) + 1
        usage["tokens"] = usage.get("tokens", 0) + tokens
        usage["cost_usd"] = usage.get("cost_usd", 0.0) + cost
        usage["last_update"] = datetime.now().isoformat()

        self._save_usage()

    def check_quota(self, estimated_tokens: int, estimated_cost: float) -> Tuple[bool, str]:
        """
        Check if request is within quota limits.

        Returns:
            (allowed, reason)
        """
        # Check circuit breaker
        if self.circuit_open:
            if datetime.now() < self.circuit_open_until:
                return False, f"Circuit breaker open until {self.circuit_open_until}"
            else:
                self.circuit_open = False
                logger.info("Circuit breaker reset")

        # Check per-request limits
        if estimated_tokens > self.quota.max_request_tokens:
            return False, f"Request tokens ({estimated_tokens}) exceeds limit ({self.quota.max_request_tokens})"

        if estimated_cost > self.quota.max_request_cost_usd:
            return False, f"Request cost (${estimated_cost:.4f}) exceeds limit (${self.quota.max_request_cost_usd:.4f})"

        # Check daily limits
        daily = self._get_current_usage("daily")
        if daily["requests"] >= self.quota.daily_requests:
            return False, f"Daily request limit reached ({self.quota.daily_requests})"

        if daily["tokens"] + estimated_tokens > self.quota.daily_tokens:
            return False, f"Daily token limit would be exceeded ({self.quota.daily_tokens})"

        if daily["cost_usd"] + estimated_cost > self.quota.daily_cost_usd:
            return False, f"Daily cost limit would be exceeded (${self.quota.daily_cost_usd:.2f})"

        # Check hourly limits (burst protection)
        hourly = self._get_current_usage("hourly")
        if hourly["requests"] >= self.quota.hourly_requests:
            return False, f"Hourly request limit reached ({self.quota.hourly_requests})"

        if hourly["tokens"] + estimated_tokens > self.quota.hourly_tokens:
            return False, f"Hourly token limit would be exceeded ({self.quota.hourly_tokens})"

        return True, "OK"

    def record_usage(
        self,
        provider: ProviderType,
        request_tokens: int,
        response_tokens: int,
        cost: float,
        duration_ms: int,
        status: str = "success",
        metadata: Optional[Dict] = None,
    ):
        """Record actual usage."""
        total_tokens = request_tokens + response_tokens

        # Update usage counters
        self._update_usage(total_tokens, cost, "daily")
        self._update_usage(total_tokens, cost, "hourly")

        # Create usage record
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            provider=provider.value,
            request_tokens=request_tokens,
            response_tokens=response_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            duration_ms=duration_ms,
            status=status,
            metadata=metadata or {},
        )

        # Append to log file
        log_file = self.storage_path / f"usage_log_{datetime.now().strftime('%Y-%m')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

        logger.info(f"Usage recorded: {total_tokens} tokens, ${cost:.4f}")

    def trigger_circuit_breaker(self, duration_minutes: int = 30):
        """Trigger circuit breaker to prevent further requests."""
        self.circuit_open = True
        self.circuit_open_until = datetime.now() + timedelta(minutes=duration_minutes)

        logger.warning(f"🚨 Circuit breaker OPEN for {duration_minutes} minutes")

        # Write circuit breaker file
        breaker_file = self.storage_path / "circuit_breaker.json"
        with open(breaker_file, "w") as f:
            json.dump(
                {
                    "open": True,
                    "until": self.circuit_open_until.isoformat(),
                    "reason": "Automatic protection triggered",
                },
                f,
            )

    def get_usage_summary(self) -> Dict:
        """Get comprehensive usage summary."""
        daily = self._get_current_usage("daily")
        hourly = self._get_current_usage("hourly")

        return {
            "tier": self.tier.value,
            "daily": {
                "requests": daily["requests"],
                "tokens": daily["tokens"],
                "cost_usd": daily["cost_usd"],
                "limits": {
                    "requests": self.quota.daily_requests,
                    "tokens": self.quota.daily_tokens,
                    "cost_usd": self.quota.daily_cost_usd,
                },
                "usage_percent": {
                    "requests": (daily["requests"] / self.quota.daily_requests) * 100
                    if self.quota.daily_requests > 0
                    else 0,
                    "tokens": (daily["tokens"] / self.quota.daily_tokens) * 100 if self.quota.daily_tokens > 0 else 0,
                    "cost": (daily["cost_usd"] / self.quota.daily_cost_usd) * 100
                    if self.quota.daily_cost_usd > 0
                    else 0,
                },
            },
            "hourly": {
                "requests": hourly["requests"],
                "tokens": hourly["tokens"],
                "cost_usd": hourly["cost_usd"],
                "limits": {
                    "requests": self.quota.hourly_requests,
                    "tokens": self.quota.hourly_tokens,
                    "cost_usd": self.quota.hourly_cost_usd,
                },
            },
            "circuit_breaker": {
                "open": self.circuit_open,
                "until": self.circuit_open_until.isoformat() if self.circuit_open_until else None,
            },
        }

    def reset_hourly_usage(self):
        """Reset hourly usage counters."""
        self.hourly_usage = {}
        self._save_usage()
        logger.info("Hourly usage reset")

    def reset_daily_usage(self):
        """Reset daily usage counters."""
        self.daily_usage = {}
        self._save_usage()
        logger.info("Daily usage reset")


class ResourceMonitor:
    """Monitor Alibaba Cloud instance resources."""

    def __init__(self, quota: UsageQuota):
        self.quota = quota

    def check_resources(self) -> Tuple[bool, str]:
        """
        Check if instance resources are within limits.

        Returns:
            (healthy, message)
        """
        try:
            import psutil

            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.quota.max_cpu_percent:
                return False, f"CPU usage high: {cpu_percent:.1f}% > {self.quota.max_cpu_percent}%"

            # Check Memory
            memory = psutil.virtual_memory()
            if memory.percent > self.quota.max_memory_percent:
                return False, f"Memory usage high: {memory.percent:.1f}% > {self.quota.max_memory_percent}%"

            # Check Disk
            disk = psutil.disk_usage("/")
            if disk.percent > self.quota.max_disk_percent:
                return False, f"Disk usage high: {disk.percent:.1f}% > {self.quota.max_disk_percent}%"

            return True, "Resources healthy"

        except ImportError:
            logger.warning("psutil not installed - skipping resource check")
            return True, "Resource check skipped"
        except Exception as e:
            logger.error(f"Resource check error: {e}")
            return True, f"Resource check error: {e}"


# Predefined quotas for different tiers
TIER_QUOTAS = {
    TierLevel.FREE: UsageQuota(
        daily_requests=50,
        daily_tokens=25000,
        daily_cost_usd=0.25,
        hourly_requests=10,
        hourly_tokens=5000,
        hourly_cost_usd=0.05,
        max_request_tokens=2000,
        max_response_tokens=1000,
        max_request_cost_usd=0.02,
    ),
    TierLevel.ECONOMY: UsageQuota(
        daily_requests=100,
        daily_tokens=50000,
        daily_cost_usd=0.50,
        hourly_requests=20,
        hourly_tokens=10000,
        hourly_cost_usd=0.10,
        max_request_tokens=4000,
        max_response_tokens=2000,
        max_request_cost_usd=0.05,
    ),
    TierLevel.STANDARD: UsageQuota(
        daily_requests=300,
        daily_tokens=150000,
        daily_cost_usd=2.00,
        hourly_requests=50,
        hourly_tokens=30000,
        hourly_cost_usd=0.35,
        max_request_tokens=8000,
        max_response_tokens=4000,
        max_request_cost_usd=0.15,
    ),
    TierLevel.PREMIUM: UsageQuota(
        daily_requests=500,
        daily_tokens=300000,
        daily_cost_usd=5.00,
        hourly_requests=100,
        hourly_tokens=60000,
        hourly_cost_usd=0.75,
        max_request_tokens=16000,
        max_response_tokens=8000,
        max_request_cost_usd=0.30,
    ),
}


def get_credit_manager(tier: str = "free") -> CreditProtectionManager:
    """Get configured credit manager for tier."""
    tier_level = TierLevel(tier.lower())
    quota = TIER_QUOTAS[tier_level]

    storage_path = os.getenv("CREDIT_PROTECTION_PATH", "/var/lib/vaal/credit_protection")

    return CreditProtectionManager(quota=quota, storage_path=storage_path, tier=tier_level)


# Global instance
_global_manager: Optional[CreditProtectionManager] = None


def get_manager() -> CreditProtectionManager:
    """Get global credit manager instance."""
    global _global_manager

    if _global_manager is None:
        tier = os.getenv("CREDIT_TIER", "free")
        _global_manager = get_credit_manager(tier)

    return _global_manager
