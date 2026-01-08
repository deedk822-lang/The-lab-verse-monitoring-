#!/usr/bin/env python3
"""
validate_env.py - Production Agent Validation
Validates Z.ai GLM-4.7 and Perplexity Sonar Pro connectivity
"""

import os
import sys
import json
import time
from openai import OpenAI

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
NC = "\033[0m"


def validate_zai():
    """Validates Z.ai GLM-4.7 connection"""
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        return False, "ZAI_API_KEY missing"

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

        return True, f"Z.ai Connected (model: {response.model})"

    except Exception as e:
        return False, f"Z.ai Failed: {str(e)}"


def validate_perplexity():
    """Validates Perplexity Sonar Pro connection"""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return False, "PERPLEXITY_API_KEY missing"

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

        return True, "Perplexity Connected (sonar-pro)"

    except Exception as e:
        return False, f"Perplexity Failed: {str(e)}"


def main():
    """Main validation entry point"""
    print("🔍 Validating Agent Stack...")

    # Validate Z.ai
    z_ok, z_msg = validate_zai()
    if z_ok:
        print(f"{GREEN}✓ {z_msg}{NC}")
    else:
        print(f"{RED}✗ {z_msg}{NC}")

    # Validate Perplexity
    p_ok, p_msg = validate_perplexity()
    if p_ok:
        print(f"{GREEN}✓ {p_msg}{NC}")
    else:
        print(f"{RED}✗ {p_msg}{NC}")

    # Exit code
    if z_ok and p_ok:
        print(f"\n{GREEN}✓ All validations passed{NC}")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Validation failed{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
