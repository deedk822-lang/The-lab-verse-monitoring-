#!/usr/bin/env python3
"""
VAAL AI Empire - Credit Dashboard
Real-time monitoring dashboard for credit usage
"""

import sys
from datetime import datetime
from credit_manager import CreditManager


def get_status_emoji(percentage: float) -> str:
    """Get status emoji based on percentage"""
    if percentage < 50:
        return "🟢"
    elif percentage < 75:
        return "🟡"
    elif percentage < 90:
        return "🟠"
    else:
        return "🔴"


def get_progress_bar(percentage: float, width: int = 30) -> str:
    """Generate ASCII progress bar"""
    filled = int((percentage / 100) * width)
    return "█" * filled + "░" * (width - filled)


def print_header():
    """Print dashboard header"""
    print("=" * 70)
    print("" + " " * 14 + "VAAL AI EMPIRE - CREDIT PROTECTION DASHBOARD" + " " * 10 + "")
    print("=" * 70)


def print_usage_line(label: str, current: float, limit: float, unit: str, is_cost: bool = False):
    """Print a single usage line with progress bar"""
    percentage = (current / limit * 100) if limit > 0 else 0
    emoji = get_status_emoji(percentage)
    bar = get_progress_bar(percentage)

    if is_cost:
        print(f"{label:12} ${current:7.4f} / ${limit:5.2f}  {emoji}{bar} {percentage:5.1f}%")
    elif unit == "":
        print(f"{label:12} {current:5.0f} / {limit:5.0f}  {emoji}{bar} {percentage:5.1f}%")
    else:
        print(f"{label:12} {current:7.0f} / {limit:7.0f}  {emoji}{bar} {percentage:5.1f}%")


def get_overall_status(percentage: float) -> tuple:
    """Get overall status message"""
    if percentage < 50:
        return "🟢", "HEALTHY", "Usage at safe level"
    elif percentage < 75:
        return "🟡", "MODERATE", "Monitor usage closely"
    elif percentage < 90:
        return "🟠", "HIGH", "Approaching limits"
    else:
        return "🔴", "CRITICAL", "Immediate action required"


def main():
    """Main dashboard function"""
    # Get parameters
    tier = sys.argv[1] if len(sys.argv) > 1 else "free"
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/vaal_credits"

    # Initialize manager
    try:
        manager = CreditManager(tier=tier, data_dir=data_dir)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1

    # Get summary
    summary = manager.get_usage_summary()

    # Print dashboard
    print_header()
    print()
    print(f"Tier: {tier.upper()}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Circuit breaker status
    if summary["circuit_breaker"]["active"]:
        print("🔴 CIRCUIT BREAKER: ACTIVE (System blocked)")
        print(f"   Reason: {summary['circuit_breaker']['reason']}")
    else:
        print("🟢 CIRCUIT BREAKER: CLOSED (System operational)")
    print()

    # Daily usage
    print("-" * 70)
    print("DAILY USAGE:")
    print("-" * 70)
    daily = summary["daily"]
    print_usage_line(
        "Requests:",
        daily["usage"]["requests"],
        daily["limits"]["requests"],
        ""
    )
    print_usage_line(
        "Tokens:",
        daily["usage"]["tokens"],
        daily["limits"]["tokens"],
        "tokens"
    )
    print_usage_line(
        "Cost:",
        daily["usage"]["cost"],
        daily["limits"]["cost"],
        "$",
        is_cost=True
    )
    print()

    # Overall status
    emoji, status, message = get_overall_status(daily["percentages"]["cost"])
    print(f"{emoji} Status: {status} - {message}")
    print()

    # Hourly usage
    print("-" * 70)
    print("HOURLY USAGE:")
    print("-" * 70)
    hourly = summary["hourly"]
    print(f"Requests:   {hourly['usage']['requests']:>3} / {hourly['limits']['requests']:>3}")
    print(f"Tokens:     {hourly['usage']['tokens']:>5} / {hourly['limits']['tokens']:>5}")
    print(f"Cost:      ${hourly['usage']['cost']:>6.4f} / ${hourly['limits']['cost']:>5.2f}")
    print()

    # Footer
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print(f"Run: vaal-dashboard [tier] [data_dir]")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())