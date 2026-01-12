#!/usr/bin/env python3
"""
validate_env.py - Production Agent Validation
Validates Z.ai GLM-4.7 and Perplexity Sonar Pro connectivity
"""

import os
import sys
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
NC = '\033[0m'


def validate_zai():
    """Validates Z.ai GLM-4.7 connection"""
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        return False, "ZAI_API_KEY missing from environment"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.z.ai/api/paas/v4/"
        )

        response = client.chat.completions.create(
            model="glm-4.7",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
    except Exception as e:
        error_msg = str(e)

        # Check for specific error codes
        if "429" in error_msg or "Insufficient balance" in error_msg:
            return False, (
                "Z.ai Failed: Insufficient balance or no resource package (HTTP 429). "
                "Please recharge account at https://api.z.ai"
            )
        elif "401" in error_msg or "Unauthorized" in error_msg:
            return False, "Z.ai Failed: Invalid API key (HTTP 401)"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return False, "Z.ai Failed: Access forbidden (HTTP 403)"
        else:
            return False, f"Z.ai Failed: {error_msg}"
    else:
        return True, f"Z.ai Connected (model: {response.model})"


def validate_perplexity():
    """Validates Perplexity Sonar Pro connection"""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return False, "PERPLEXITY_API_KEY missing from environment"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
    except Exception as e:
        error_msg = str(e)

        # Check for specific error codes
        if "429" in error_msg:
            return False, "Perplexity Failed: Rate limit exceeded (HTTP 429)"
        elif "401" in error_msg or "Unauthorized" in error_msg:
            return False, "Perplexity Failed: Invalid API key (HTTP 401)"
        elif "403" in error_msg:
            return False, "Perplexity Failed: Access forbidden (HTTP 403)"
        else:
            return False, f"Perplexity Failed: {error_msg}"
    else:
        return True, "Perplexity Connected (sonar-pro)"


def main():
    """Main validation entry point"""
    print("🔍 Validating Agent Stack...")
    print()

    all_passed = True

    # Validate Z.ai
    z_ok, z_msg = validate_zai()
    if z_ok:
        print(f"{GREEN}✓ {z_msg}{NC}")
    else:
        print(f"{RED}✗ {z_msg}{NC}")
        all_passed = False

    # Validate Perplexity
    p_ok, p_msg = validate_perplexity()
    if p_ok:
        print(f"{GREEN}✓ {p_msg}{NC}")
    else:
        print(f"{RED}✗ {p_msg}{NC}")
        all_passed = False

    print()

    # Exit with appropriate status
    if all_passed:
        print(f"{GREEN}✓ All validations passed{NC}")
        sys.exit(0)
    else:
        print(f"{RED}✗ Validation failed{NC}")
        print()
        print(f"{YELLOW}⚠ Action Required:{NC}")
        if not z_ok and "429" in z_msg:
            print(f"  • Recharge Z.ai account at https://api.z.ai/console")
        if not p_ok and "429" in p_msg:
            print(f"  • Check Perplexity rate limits at https://www.perplexity.ai/settings/api")
        sys.exit(1)


if __name__ == "__main__":
    main()
