#!/usr/bin/env python3
"""
validate_env.py - Production Agent Validation
Validates Z.ai GLM-4.7 and Perplexity Sonar Pro connectivity
"""

import os
import sys
from openai import OpenAI, APIStatusError, APIConnectionError
from config import PERPLEXITY_API_BASE_URL, PERPLEXITY_MODEL, ZAI_API_BASE_URL, ZAI_MODEL

# Fail fast if dependencies are missing
try:
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Python Dependency Error: {e}")
    print("Run: pip install python-dotenv openai")
    sys.exit(1)

load_dotenv()

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
NC = "\033[0m"

def log_success(msg):
    """Logs a success message in green."""
    print(f"{GREEN}✓ {msg}{NC}")

def log_fail(msg):
    """Logs a failure message in red."""
    print(f"{RED}✗ {msg}{NC}")

def validate_zai():
    """Validates Z.ai GLM-4.7 connection"""
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        return False, "ZAI_API_KEY missing"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=ZAI_API_BASE_URL
        )
        response = client.chat.completions.create(
            model=ZAI_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        return True, f"Z.ai Connected (model: {response.model})"
    except APIStatusError as e:
        if e.status_code == 429:
            return False, "Z.ai Failed: Insufficient balance or no resource package."
        return False, f"Z.ai Failed: {e}"
    except APIConnectionError as e:
        return False, f"Z.ai Connection Failed: {e}"
    except Exception as e:
        return False, f"Z.ai Failed: An unexpected error occurred: {e}"

def validate_perplexity():
    """Validates Perplexity Sonar Pro connection"""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return False, "PERPLEXITY_API_KEY missing"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=PERPLEXITY_API_BASE_URL
        )
        response = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        return True, f"Perplexity Connected (model: {response.model})"
    except APIStatusError as e:
        return False, f"Perplexity Failed: {e}"
    except APIConnectionError as e:
        return False, f"Perplexity Connection Failed: {e}"
    except Exception as e:
        return False, f"Perplexity Failed: An unexpected error occurred: {e}"

def main():
    """Main validation entry point"""
    print("🔍 Validating Agent Stack...")
    has_error = False

    # Validate Z.ai
    z_ok, z_msg = validate_zai()
    if z_ok:
        log_success(z_msg)
    else:
        log_fail(z_msg)
        has_error = True

    # Validate Perplexity
    p_ok, p_msg = validate_perplexity()
    if p_ok:
        log_success(p_msg)
    else:
        log_fail(p_msg)
        has_error = True

    # Exit code
    if not has_error:
        print(f"\n{GREEN}✓ All validations passed{NC}")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Validation failed{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
