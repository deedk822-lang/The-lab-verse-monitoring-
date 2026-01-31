#!/usr/bin/env python3
"""
VAAL AI Empire - Credit Protection Dashboard
Real-time monitoring dashboard for credit usage
"""

import sys
from datetime import datetime

from credit_manager import CreditManager


def print_bar(percentage: float, width: int = 30) -> str:
    """Print a progress bar"""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)

    if percentage >= 95:
        color = "\033[91m"  # Red
    elif percentage >= 75:
        color = "\033[93m"  # Yellow
    else:
        color = "\033[92m"  # Green

    reset = "\033[0m"
    return f"{color}{bar}{reset} {percentage:.1f}%"

def get_status_emoji(percentage: float) -> str:
    """Get status emoji based on percentage"""
    if percentage >= 95:
        return "🔴"
    elif percentage >= 90:
        return "🟠"
    elif percentage >= 75:
        return "🟡"
    else:
        return "🟢"

def main():
    """Main dashboard function"""
    # Parse arguments
    tier = "free"
    data_dir = "/tmp/vaal_credits"

    if len(sys.argv) > 1:
        tier = sys.argv[1]
    if len(sys.argv) > 2:
        data_dir = sys.argv[2]

    # Initialize manager
    try:
        manager = CreditManager(tier=tier, data_dir=data_dir)
    except Exception as e:
        print(f"Error initializing credit manager: {e}")
        sys.exit(1)

    # Get usage summary
    summary = manager.get_usage_summary()

    # Clear screen
    print("\033[2J\033[H")

    # Header
    print("=" * 70)
    print(" VAAL AI EMPIRE - CREDIT PROTECTION DASHBOARD".center(70))
    print("=" * 70)
    print()

    # Tier and status
    print(f"Tier: {summary['tier'].upper()}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Circuit breaker status
    if summary['circuit_breaker']['active']:
        print("🔴 CIRCUIT BREAKER: ACTIVE")
        print(f"   Reason: {summary['circuit_breaker']['reason']}")
        print()
    else:
        print("🟢 CIRCUIT BREAKER: CLOSED (System operational)")
        print()

    # Daily usage
    print("-" * 70)
    print("DAILY USAGE:")
    print("-" * 70)

    daily = summary['daily']

    # Requests
    req_pct = daily['percentages']['requests']
    print(f"Requests: {daily['usage']['requests']:3d} / {daily['limits']['requests']:3d}  ", end="")
    print(print_bar(req_pct))

    # Tokens
    tok_pct = daily['percentages']['tokens']
    print(f"Tokens:   {daily['usage']['tokens']:6d} / {daily['limits']['tokens']:6d}  ", end="")
    print(print_bar(tok_pct))

    # Cost
    cost_pct = daily['percentages']['cost']
    print(f"Cost:     ${daily['usage']['cost']:6.4f} / ${daily['limits']['cost']:5.2f}  ", end="")
    print(print_bar(cost_pct))
    print()

    # Overall status
    max_pct = max(req_pct, tok_pct, cost_pct)
    status_emoji = get_status_emoji(max_pct)

    if max_pct >= 95:
        status_text = "CRITICAL - Circuit breaker will trigger!"
    elif max_pct >= 90:
        status_text = "WARNING - Approaching daily limit"
    elif max_pct >= 75:
        status_text = "CAUTION - Monitor usage closely"
    else:
        status_text = "HEALTHY - Usage at safe level"

    print(f"{status_emoji} Status: {status_text}")
    print()

    # Hourly usage
    print("-" * 70)
    print("HOURLY USAGE:")
    print("-" * 70)

    hourly = summary['hourly']
    print(f"Requests:   {hourly['usage']['requests']:3d} / {hourly['limits']['requests']:3d}")
    print(f"Tokens:     {hourly['usage']['tokens']:6d} / {hourly['limits']['tokens']:6d}")
    print(f"Cost:       ${hourly['usage']['cost']:6.4f} / ${hourly['limits']['cost']:5.2f}")
    print()

    # Recommendations
    if max_pct >= 90:
        print("-" * 70)
        print("⚠️  RECOMMENDATIONS:")
        print("-" * 70)
        print("• Reduce request frequency")
        print("• Use shorter prompts")
        print("• Consider upgrading tier")
        print("• Monitor dashboard frequently")
        print()

    # Footer
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print("Run: python credit_dashboard.py [tier] [data_dir]")
    print("=" * 70)

if __name__ == "__main__":
    main()
