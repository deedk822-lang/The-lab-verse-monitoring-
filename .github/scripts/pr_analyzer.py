#!/usr/bin/env python3
"""Minimal PR analyzer used by Jules Governance.

Reads a newline-separated list of changed file paths from stdin and emits a short
report. This script is intentionally non-blocking and should not fail PRs.
"""

import sys

def main() -> int:
    raw = sys.stdin.read().strip()
    files = [f for f in raw.splitlines() if f.strip()]

    print("Changed files:")
    if not files:
        print("- (none)")
    else:
        for f in files:
            print(f"- {f}")

    # Always exit 0 so governance is informational.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
