"""
Credit Protection Package
Prevents runaway costs on cloud instances.
"""

from vaal_ai_empire.credit_protection.manager import (
    TIER_QUOTAS,
    CreditProtectionManager,
    ProviderType,
    ResourceMonitor,
    TierLevel,
    UsageQuota,
    UsageRecord,
    get_credit_manager,
    get_manager,
)

__all__ = [
    "TIER_QUOTAS",
    "CreditProtectionManager",
    "ProviderType",
    "ResourceMonitor",
    "TierLevel",
    "UsageQuota",
    "UsageRecord",
    "get_credit_manager",
    "get_manager",
]
