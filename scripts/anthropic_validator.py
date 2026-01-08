#!/usr/bin/env python3
"""
Anthropic API validation with Claude 4.5 support.

This module validates Anthropic API connectivity and API key validity
using the official Anthropic Python SDK with proper error handling.
"""

import os
import sys
import logging
from typing import Tuple
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
NC = "\033[0m"


def validate_anthropic_api() -> Tuple[bool, str]:
    """
    Validate Anthropic API key and connectivity.

    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return False, "ANTHROPIC_API_KEY environment variable not set"

    if not api_key.startswith("sk-ant-"):
        return False, "API key format invalid (should start with 'sk-ant-')"

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Test with lightweight request
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        return True, f"✓ Connected to {message.model}"

    except anthropic.AuthenticationError:
        return False, "Invalid API key or unauthorized"
    except anthropic.PermissionDeniedError:
        return False, "API key lacks required permissions"
    except anthropic.RateLimitError:
        return False, "Rate limit exceeded - try again later"
    except anthropic.APIConnectionError as e:
        return False, f"Connection failed: {e}"
    except anthropic.APIStatusError as e:
        return False, f"API error {e.status_code}: {e.message}"
    except anthropic.APIError as e:
        return False, f"API error: {e}"
    except Exception as e:
        logger.exception("Unexpected error validating Anthropic API")
        return False, f"Unexpected error: {type(e).__name__}"


def main() -> int:
    """CLI entry point."""
    print("🔍 Validating Anthropic API...")

    is_valid, message = validate_anthropic_api()

    if is_valid:
        print(f"{GREEN}{message}{NC}")
        return 0
    else:
        print(f"{RED}✗ {message}{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
