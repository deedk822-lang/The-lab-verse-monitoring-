#!/usr/bin/env python3
"""Minimal PR analyzer used by Jules Governance.

Reads a newline-separated list of changed file paths from stdin and emits a short
report. This script is intentionally non-blocking and should not fail PRs.
"""

import sys


def main() -> int:
    """
    Produce a short report of changed file paths read from standard input.
    
    Reads a newline-separated list of file paths from stdin, ignores empty lines, and prints a "Changed files:" header followed by each path prefixed with "- ". If no paths are provided, prints "- (none)".
    
    Returns:
        int: `0` to indicate successful, informational execution.
    """
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
