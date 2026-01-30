#!/usr/bin/env python3
"""
VAAL AI Empire - Credit Protection Manager
Real working implementation for Alibaba Cloud free tier protection
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CreditManager:
    """Production credit management system"""
    
    # Tier configurations with REAL limits
    TIERS = {
        "free": {
            "daily_max_requests": 50,
            "daily_max_tokens": 25000,
            "daily_max_cost": 0.25,
            "hourly_max_requests": 10,
            "hourly_max_tokens": 5000,
            "hourly_max_cost": 0.05,
            "max_tokens_per_request": 2000,
            "max_cost_per_request": 0.02
        },
        "economy": {
            "daily_max_requests": 100,
            "daily_max_tokens": 50000,
            "daily_max_cost": 0.50,
            "hourly_max_requests": 20,
            "hourly_max_tokens": 10000,
            "hourly_max_cost": 0.10,
            "max_tokens_per_request": 4000,
            "max_cost_per_request": 0.04
        },
        "standard": {
            "daily_max_requests": 300,
            "daily_max_tokens": 150000,
            "daily_max_cost": 2.00,
            "hourly_max_requests": 50,
            "hourly_max_tokens": 25000,
            "hourly_max_cost": 0.25,
            "max_tokens_per_request": 8000,
            "max_cost_per_request": 0.10
        },
        "premium": {
            "daily_max_requests": 500,
            "daily_max_tokens": 250000,
            "daily_max_cost": 5.00,
            "hourly_max_requests": 100,
            "hourly_max_tokens": 50000,
            "hourly_max_cost": 0.50,
            "max_tokens_per_request": 16000,
            "max_cost_per_request": 0.20
        }
    }

    def __init__(self, tier: str = "free", data_dir: str = "/tmp/vaal_credits"):
        """Initialize credit manager with actual file storage"""
        self.tier = tier.lower()
        if self.tier not in self.TIERS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(self.TIERS.keys())}")
        
        self.config = self.TIERS[self.tier]
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.daily_file = self.data_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.json"
        self.hourly_file = self.data_dir / f"hourly_{datetime.now().strftime('%Y%m%d_%H')}.json"
        self.circuit_file = self.data_dir / "circuit_breaker.json"
        self.log_file = self.data_dir / f"usage_log_{datetime.now().strftime('%Y%m')}.jsonl"
        
        logger.info(f"CreditManager initialized: tier={tier}, data_dir={data_dir}")

    def _load_usage(self, filepath: Path) -> Dict:
        """Load usage data from file"""
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
        
        return {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "last_updated": datetime.now().isoformat()
        }

    def _save_usage(self, filepath: Path, data: Dict):
        """Save usage data to file"""
        data["last_updated"] = datetime.now().isoformat()
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")

    def _log_request(self, tokens: int, cost: float, allowed: bool, reason: str = ""):
        """Log each request to JSONL file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tier": self.tier,
            "tokens": tokens,
            "cost": cost,
            "allowed": allowed,
            "reason": reason
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging request: {e}")

    def check_circuit_breaker(self) -> Tuple[bool, str]:
        """Check if circuit breaker is active"""
        if not self.circuit_file.exists():
            return False, ""
        
        try:
            with open(self.circuit_file, 'r') as f:
                cb_data = json.load(f)
            
            triggered_at = datetime.fromisoformat(cb_data["triggered_at"])
            cooldown_minutes = cb_data.get("cooldown_minutes", 60)
            
            if datetime.now() < triggered_at + timedelta(minutes=cooldown_minutes):
                reason = cb_data.get("reason", "Circuit breaker active")
                return True, reason
            else:
                # Cooldown expired, remove circuit breaker
                self.circuit_file.unlink()
                logger.info("Circuit breaker cooldown expired, removed")
                return False, ""
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return False, ""

    def trigger_circuit_breaker(self, reason: str, cooldown_minutes: int = 60):
        """Trigger circuit breaker"""
        cb_data = {
            "triggered_at": datetime.now().isoformat(),
            "reason": reason,
            "cooldown_minutes": cooldown_minutes,
            "tier": self.tier
        }
        
        try:
            with open(self.circuit_file, 'w') as f:
                json.dump(cb_data, f, indent=2)
            logger.warning(f"Circuit breaker triggered: {reason}")
        except Exception as e:
            logger.error(f"Error triggering circuit breaker: {e}")

    def estimate_cost(self, tokens: int, model: str = "kimi") -> float:
        """Estimate cost based on tokens and model"""
        # Real pricing (approximate)
        pricing = {
            "kimi": 0.00001,  # $0.01 per 1k tokens
            "qwen": 0.000005,  # $0.005 per 1k tokens
            "huggingface": 0.000002  # $0.002 per 1k tokens (free tier)
        }
        
        rate = pricing.get(model.lower(), 0.00001)
        return tokens * rate

    def can_make_request(self, estimated_tokens: int, model: str = "kimi") -> Tuple[bool, str, Dict]:
        """
        Check if request can be made within all limits
        Returns: (allowed: bool, reason: str, usage_info: dict)
        """
        # Check circuit breaker first
        breaker_active, breaker_reason = self.check_circuit_breaker()
        if breaker_active:
            return False, f"Circuit breaker active: {breaker_reason}", {}
        
        # Estimate cost
        estimated_cost = self.estimate_cost(estimated_tokens, model)
        
        # Load current usage
        daily_usage = self._load_usage(self.daily_file)
        hourly_usage = self._load_usage(self.hourly_file)
        
        # Check per-request limits
        if estimated_tokens > self.config["max_tokens_per_request"]:
            reason = f"Request exceeds max tokens per request: {estimated_tokens} > {self.config['max_tokens_per_request']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        if estimated_cost > self.config["max_cost_per_request"]:
            reason = f"Request exceeds max cost per request: ${estimated_cost:.4f} > ${self.config['max_cost_per_request']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        # Check hourly limits
        if hourly_usage["requests"] + 1 > self.config["hourly_max_requests"]:
            reason = f"Hourly request limit reached: {hourly_usage['requests']}/{self.config['hourly_max_requests']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        if hourly_usage["tokens"] + estimated_tokens > self.config["hourly_max_tokens"]:
            reason = f"Hourly token limit would be exceeded: {hourly_usage['tokens'] + estimated_tokens} > {self.config['hourly_max_tokens']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        if hourly_usage["cost"] + estimated_cost > self.config["hourly_max_cost"]:
            reason = f"Hourly cost limit would be exceeded: ${hourly_usage['cost'] + estimated_cost:.4f} > ${self.config['hourly_max_cost']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        # Check daily limits
        if daily_usage["requests"] + 1 > self.config["daily_max_requests"]:
            reason = f"Daily request limit reached: {daily_usage['requests']}/{self.config['daily_max_requests']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        if daily_usage["tokens"] + estimated_tokens > self.config["daily_max_tokens"]:
            reason = f"Daily token limit would be exceeded: {daily_usage['tokens'] + estimated_tokens} > {self.config['daily_max_tokens']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        if daily_usage["cost"] + estimated_cost > self.config["daily_max_cost"]:
            reason = f"Daily cost limit would be exceeded: ${daily_usage['cost'] + estimated_cost:.4f} > ${self.config['daily_max_cost']}"
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        # Check if approaching circuit breaker threshold (95%)
        daily_usage_pct = (daily_usage["cost"] / self.config["daily_max_cost"]) * 100
        if daily_usage_pct >= 95:
            reason = f"Daily usage at {daily_usage_pct:.1f}%, triggering circuit breaker"
            self.trigger_circuit_breaker(reason)
            self._log_request(estimated_tokens, estimated_cost, False, reason)
            return False, reason, daily_usage
        
        # All checks passed
        self._log_request(estimated_tokens, estimated_cost, True, "OK")
        return True, "OK", daily_usage

    def record_usage(self, actual_tokens: int, model: str = "kimi"):
        """Record actual usage after request completes"""
        actual_cost = self.estimate_cost(actual_tokens, model)
        
        # Update daily usage
        daily_usage = self._load_usage(self.daily_file)
        daily_usage["requests"] += 1
        daily_usage["tokens"] += actual_tokens
        daily_usage["cost"] += actual_cost
        self._save_usage(self.daily_file, daily_usage)
        
        # Update hourly usage
        hourly_usage = self._load_usage(self.hourly_file)
        hourly_usage["requests"] += 1
        hourly_usage["tokens"] += actual_tokens
        hourly_usage["cost"] += actual_cost
        self._save_usage(self.hourly_file, hourly_usage)
        
        logger.info(f"Recorded usage: {actual_tokens} tokens, ${actual_cost:.4f}")
        
        # Check alert thresholds
        daily_pct = (daily_usage["cost"] / self.config["daily_max_cost"]) * 100
        if daily_pct >= 90:
            logger.warning(f"🚨 CRITICAL: Daily usage at {daily_pct:.1f}%!")
        elif daily_pct >= 75:
            logger.warning(f"⚠️ WARNING: Daily usage at {daily_pct:.1f}%")

    def get_usage_summary(self) -> Dict:
        """Get current usage summary"""
        daily_usage = self._load_usage(self.daily_file)
        hourly_usage = self._load_usage(self.hourly_file)
        breaker_active, breaker_reason = self.check_circuit_breaker()
        
        return {
            "tier": self.tier,
            "circuit_breaker": {
                "active": breaker_active,
                "reason": breaker_reason
            },
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
            }
        }

    def reset_daily(self):
        """Reset daily counters (called by cron at midnight)"""
        if self.daily_file.exists():
            # Archive old file
            archive_name = self.daily_file.stem + "_archived" + self.daily_file.suffix
            archive_path = self.data_dir / archive_name
            self.daily_file.rename(archive_path)
            logger.info(f"Daily usage reset, archived to {archive_path}")

    def reset_hourly(self):
        """Reset hourly counters (called by cron every hour)"""
        if self.hourly_file.exists():
            self.hourly_file.unlink()
            logger.info("Hourly usage reset")


if __name__ == "__main__":
    # Test the credit manager
    print("Testing Credit Manager...")
    
    manager = CreditManager(tier="free")
    
    # Test 1: Check if we can make a request
    print("\n=== Test 1: Check if we can make a request ===")
    allowed, reason, usage = manager.can_make_request(1000, "kimi")
    print(f"Allowed: {allowed}")
    print(f"Reason: {reason}")
    
    # Test 2: Record usage
    if allowed:
        print("\n=== Test 2: Record usage ===")
        manager.record_usage(1000, "kimi")
        print("Usage recorded")
    
    # Test 3: Get summary
    print("\n=== Test 3: Get usage summary ===")
    summary = manager.get_usage_summary()
    print(json.dumps(summary, indent=2))
    
    # Test 4: Simulate hitting daily limit
    print("\n=== Test 4: Simulate approaching limit ===")
    for i in range(45):  # Simulate 45 more requests
        manager.record_usage(500, "kimi")
    
    summary = manager.get_usage_summary()
    print(f"Daily usage: {summary['daily']['usage']['requests']}/{summary['daily']['limits']['requests']} requests")
    print(f"Daily cost: ${summary['daily']['usage']['cost']:.4f}/${summary['daily']['limits']['cost']}")
    print(f"Cost percentage: {summary['daily']['percentages']['cost']:.1f}%")
    
    # Test 5: Try to make request near limit
    print("\n=== Test 5: Try request near limit ===")
    allowed, reason, usage = manager.can_make_request(1000, "kimi")
    print(f"Allowed: {allowed}")
    print(f"Reason: {reason}")
