"""
Credit Protection Package
Prevents runaway costs on cloud instances.
"""

from vaal_ai_empire.credit_protection.manager import (
    CreditProtectionManager,
    ResourceMonitor,
    TierLevel,
    ProviderType,
    UsageQuota,
    UsageRecord,
    TIER_QUOTAS,
    get_credit_manager,
    get_manager,
)

__all__ = [
    "CreditProtectionManager",
    "ResourceMonitor",
    "TierLevel",
    "ProviderType",
    "UsageQuota",
    "UsageRecord",
    "TIER_QUOTAS",
    "get_credit_manager",
    "get_manager",
]
