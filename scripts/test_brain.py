#!/usr/bin/env python3
"""
scripts/test_brain.py - End-to-end test for the AI brain workflow
"""

import os
import sys
from openai import OpenAI

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
    try:
        perplexity = OpenAI(api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")
        zai = OpenAI(api_key=os.getenv("ZAI_API_KEY"), base_url="https://api.z.ai/api/paas/v4/")
    except Exception as e:
        print(f"❌ API client initialization failed: {e}")
        sys.exit(1)

    # Step 1: Research with Perplexity
    print("🔎 Researching...")
    try:
        response = perplexity.chat.completions.create(
            model="sonar-pro",
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
            model="glm-4.7",
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
