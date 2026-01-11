#!/usr/bin/env python3
"""
scripts/test_brain.py - End-to-end test for the AI brain workflow
"""

import os
import sys
from openai import OpenAI
from config import PERPLEXITY_API_BASE_URL, PERPLEXITY_MODEL, ZAI_API_BASE_URL, ZAI_MODEL

# Fail fast if dependencies are missing
try:
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Python Dependency Error: {e}")
    print("Run: pip install python-dotenv openai")
    sys.exit(1)

load_dotenv()

def main():
    """Main entry point for the brain test script."""
    # Initialize clients
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    zai_key = os.getenv("ZAI_API_KEY")
    if not perplexity_key or not zai_key:
        print("❌ Missing API keys: PERPLEXITY_API_KEY and/or ZAI_API_KEY")
        sys.exit(1)

    try:
        perplexity = OpenAI(api_key=perplexity_key, base_url=PERPLEXITY_API_BASE_URL)
        zai = OpenAI(api_key=zai_key, base_url=ZAI_API_BASE_URL)
    except Exception as e:
        print(f"❌ API client initialization failed: {e}")
        sys.exit(1)

    # Step 1: Research with Perplexity
    print("🔎 Researching...")
    try:
        response = perplexity.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            max_tokens=50
        )
        if not response.choices or not response.choices[0].message:
            print("❌ Invalid response from Perplexity")
            sys.exit(1)
        fact = response.choices[0].message.content
    except Exception as e:
        print(f"❌ Perplexity API request failed: {e}")
        sys.exit(1)

    # Step 2: Reasoning with Z.ai
    print("🧠 Analyzing...")
    try:
        response = zai.chat.completions.create(
            model=ZAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Based on the fact: '{fact}', what is the capital of France?"}
            ],
            max_tokens=50
        )
        if not response.choices or not response.choices[0].message:
            print("❌ Invalid response from Z.ai")
            sys.exit(1)
        output = response.choices[0].message.content
    except Exception as e:
        print(f"❌ Z.ai API request failed: {e}")
        sys.exit(1)

    # Validate output
    if output and output.strip() and "paris" in output.lower():
        print(f"✅ Workflow passed: {output}")
        sys.exit(0)
    else:
        print(f"❌ Invalid output: {output}")
        sys.exit(1)

if __name__ == "__main__":
    main()
