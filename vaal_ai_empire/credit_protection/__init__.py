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
