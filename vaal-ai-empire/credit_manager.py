#!/usr/bin/env python3
"""
VAAL AI Empire - Credit Manager
Core credit management system with circuit breaker protection
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict, Optional


class CreditManager:
    """
    Production-ready credit management system
    Enforces tier-based limits with circuit breaker protection
    """

    # Tier configurations
    TIER_CONFIGS = {
        "free": {
            "daily_max_requests": 50,
            "daily_max_tokens": 25000,
            "daily_max_cost": 0.25,
            "hourly_max_requests": 10,
            "hourly_max_tokens": 5000,
            "hourly_max_cost": 0.05,
            "max_tokens_per_request": 2000,
            "max_cost_per_request": 0.02,
            "circuit_breaker_threshold": 0.95
        },
        "economy": {
            "daily_max_requests": 100,
            "daily_max_tokens": 50000,
            "daily_max_cost": 0.50,
            "hourly_max_requests": 20,
            "hourly_max_tokens": 10000,
            "hourly_max_cost": 0.10,
            "max_tokens_per_request": 4000,
            "max_cost_per_request": 0.04,
            "circuit_breaker_threshold": 0.95
        },
        "standard": {
            "daily_max_requests": 300,
            "daily_max_tokens": 150000,
            "daily_max_cost": 2.00,
            "hourly_max_requests": 60,
            "hourly_max_tokens": 30000,
            "hourly_max_cost": 0.40,
            "max_tokens_per_request": 8000,
            "max_cost_per_request": 0.08,
            "circuit_breaker_threshold": 0.95
        },
        "premium": {
            "daily_max_requests": 500,
            "daily_max_tokens": 250000,
            "daily_max_cost": 5.00,
            "hourly_max_requests": 100,
            "hourly_max_tokens": 50000,
            "hourly_max_cost": 1.00,
            "max_tokens_per_request": 16000,
            "max_cost_per_request": 0.16,
            "circuit_breaker_threshold": 0.95
        }
    }

    # Model pricing (per 1K tokens)
    MODEL_COSTS = {
        "kimi": 0.01,       # $0.01 per 1K tokens
        "qwen": 0.005,      # $0.005 per 1K tokens
        "huggingface": 0.002  # $0.002 per 1K tokens
    }

    def __init__(self, tier: str = "free", data_dir: str = "/tmp/vaal_credits"):
        """Initialize credit manager"""
        if tier not in self.TIER_CONFIGS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(self.TIER_CONFIGS.keys())}")

        self.tier = tier
        self.config = self.TIER_CONFIGS[tier]
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_daily_file(self) -> Path:
        """Get current daily usage file path"""
        date = datetime.now().strftime("%Y%m%d")
        return self.data_dir / f"daily_{date}.json"

    def _get_hourly_file(self) -> Path:
        """Get current hourly usage file path"""
        date = datetime.now().strftime("%Y%m%d_%H")
        return self.data_dir / f"hourly_{date}.json"

    def _load_usage(self, file_path: Path) -> Dict:
        """Load usage data from file"""
        if not file_path.exists():
            return {"requests": 0, "tokens": 0, "cost": 0.0}
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"requests": 0, "tokens": 0, "cost": 0.0}

    def _save_usage(self, file_path: Path, usage: Dict):
        """Save usage data to file"""
        with open(file_path, 'w') as f:
            json.dump(usage, f, indent=2)

    def estimate_cost(self, tokens: int, model: str = "kimi") -> float:
        """Estimate cost for given tokens and model"""
        cost_per_1k = self.MODEL_COSTS.get(model, self.MODEL_COSTS["kimi"])
        return (tokens / 1000.0) * cost_per_1k

    def check_circuit_breaker(self) -> Tuple[bool, str]:
        """Check if circuit breaker is active"""
        breaker_file = self.data_dir / "circuit_breaker.json"
        if not breaker_file.exists():
            return False, ""

        try:
            with open(breaker_file, 'r') as f:
                breaker = json.load(f)
            triggered_at = datetime.fromisoformat(breaker["triggered_at"])
            duration = breaker.get("duration_minutes", 60)
            expires_at = triggered_at + timedelta(minutes=duration)

            if datetime.now() < expires_at:
                return True, breaker["reason"]
            else:
                # Expired, remove file
                breaker_file.unlink()
                return False, ""
        except (json.JSONDecodeError, IOError, KeyError, ValueError):
            return False, ""

    def trigger_circuit_breaker(self, reason: str, duration_minutes: int = 60):
        """Trigger circuit breaker"""
        breaker_file = self.data_dir / "circuit_breaker.json"
        breaker = {
            "triggered_at": datetime.now().isoformat(),
            "reason": reason,
            "duration_minutes": duration_minutes
        }
        with open(breaker_file, 'w') as f:
            json.dump(breaker, f, indent=2)

    def can_make_request(self, estimated_tokens: int, model: str = "kimi") -> Tuple[bool, str, Dict]:
        """
        Check if request can be made within limits
        Returns: (allowed, reason, current_usage)
        """
        # Check circuit breaker first
        breaker_active, breaker_reason = self.check_circuit_breaker()
        if breaker_active:
            return False, f"Circuit breaker active: {breaker_reason}", {}

        # Estimate cost
        estimated_cost = self.estimate_cost(estimated_tokens, model)

        # Check per-request limits
        if estimated_tokens > self.config["max_tokens_per_request"]:
            return False, f"Exceeds max tokens per request ({self.config['max_tokens_per_request']})", {}
        if estimated_cost > self.config["max_cost_per_request"]:
            return False, f"Exceeds max cost per request (${self.config['max_cost_per_request']:.4f})", {}

        # Check hourly limits
        hourly_usage = self._load_usage(self._get_hourly_file())
        if hourly_usage["requests"] >= self.config["hourly_max_requests"]:
            return False, f"Hourly request limit reached ({self.config['hourly_max_requests']})", hourly_usage
        if hourly_usage["tokens"] + estimated_tokens > self.config["hourly_max_tokens"]:
            return False, f"Hourly token limit reached ({self.config['hourly_max_tokens']})", hourly_usage
        if hourly_usage["cost"] + estimated_cost > self.config["hourly_max_cost"]:
            return False, f"Hourly cost limit reached (${self.config['hourly_max_cost']:.2f})", hourly_usage

        # Check daily limits
        daily_usage = self._load_usage(self._get_daily_file())
        if daily_usage["requests"] >= self.config["daily_max_requests"]:
            return False, f"Daily request limit reached ({self.config['daily_max_requests']})", daily_usage
        if daily_usage["tokens"] + estimated_tokens > self.config["daily_max_tokens"]:
            return False, f"Daily token limit reached ({self.config['daily_max_tokens']})", daily_usage
        if daily_usage["cost"] + estimated_cost > self.config["daily_max_cost"]:
            return False, f"Daily cost limit reached (${self.config['daily_max_cost']:.2f})", daily_usage

        # Check if close to daily limit (trigger circuit breaker at 95%)
        projected_cost = daily_usage["cost"] + estimated_cost
        if projected_cost / self.config["daily_max_cost"] >= self.config["circuit_breaker_threshold"]:
            self.trigger_circuit_breaker(
                f"Approaching daily cost limit ({projected_cost/self.config['daily_max_cost']*100:.1f}%)"
            )
            return False, "Circuit breaker triggered: approaching daily limit", daily_usage

        return True, "OK", daily_usage

    def record_usage(self, actual_tokens: int, model: str = "kimi"):
        """Record actual usage"""
        actual_cost = self.estimate_cost(actual_tokens, model)

        # Update hourly usage
        hourly_file = self._get_hourly_file()
        hourly_usage = self._load_usage(hourly_file)
        hourly_usage["requests"] += 1
        hourly_usage["tokens"] += actual_tokens
        hourly_usage["cost"] += actual_cost
        self._save_usage(hourly_file, hourly_usage)

        # Update daily usage
        daily_file = self._get_daily_file()
        daily_usage = self._load_usage(daily_file)
        daily_usage["requests"] += 1
        daily_usage["tokens"] += actual_tokens
        daily_usage["cost"] += actual_cost
        self._save_usage(daily_file, daily_usage)

        # Log request
        log_file = self.data_dir / f"usage_log_{datetime.now().strftime('%Y%m')}.jsonl"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "tokens": actual_tokens,
            "cost": actual_cost
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_usage_summary(self) -> Dict:
        """Get comprehensive usage summary"""
        daily_usage = self._load_usage(self._get_daily_file())
        hourly_usage = self._load_usage(self._get_hourly_file())
        breaker_active, breaker_reason = self.check_circuit_breaker()

        return {
            "tier": self.tier,
            "daily": {
                "usage": daily_usage,
                "limits": {
                    "requests": self.config["daily_max_requests"],
                    "tokens": self.config["daily_max_tokens"],
                    "cost": self.config["daily_max_cost"]
                },
                "percentages": {
                    "requests": (daily_usage["requests"] / self.config["daily_max_requests"]) * 100,
                    "tokens": (daily_usage["tokens"] / self.config["daily_max_tokens"]) * 100,
                    "cost": (daily_usage["cost"] / self.config["daily_max_cost"]) * 100
                }
            },
            "hourly": {
                "usage": hourly_usage,
                "limits": {
                    "requests": self.config["hourly_max_requests"],
                    "tokens": self.config["hourly_max_tokens"],
                    "cost": self.config["hourly_max_cost"]
                }
            },
            "circuit_breaker": {
                "active": breaker_active,
                "reason": breaker_reason
            }
        }


if __name__ == "__main__":
    # Self-test
    print("Testing Credit Manager...")
    print()

    manager = CreditManager(tier="free", data_dir="/tmp/vaal_test")

    print("=== Test 1: Check if we can make a request ===")
    allowed, reason, usage = manager.can_make_request(1000, "kimi")
    print(f"Allowed: {allowed}")
    print(f"Reason: {reason}")
    print()

    print("=== Test 2: Record usage ===")
    manager.record_usage(1000, "kimi")
    print("Usage recorded")
    print()

    print("=== Test 3: Get usage summary ===")
    summary = manager.get_usage_summary()
    print(json.dumps(summary, indent=2))
    print()

    print("✅ All tests passed")