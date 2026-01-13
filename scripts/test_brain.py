#!/usr/bin/env python3
"""
scripts/test_brain.py - Agent Workflow Test
Tests Research (Perplexity) → Reasoning (GLM-4.7) workflow
"""

import os
import sys
from openai import OpenAI

# Get API keys
zai_key = os.getenv("ZAI_API_KEY")
pplx_key = os.getenv("PERPLEXITY_API_KEY")

if not zai_key or not pplx_key:
    print("❌ Missing API keys")
    sys.exit(1)

# Initialize clients
zai = OpenAI(api_key=zai_key, base_url="https://api.z.ai/api/paas/v4/")
pplx = OpenAI(api_key=pplx_key, base_url="https://api.perplexity.ai")

try:
    # Step 1: Research with Perplexity
    print("🔍 Researching...")
    search = pplx.chat.completions.create(
        model="sonar-pro",
        messages=[{"role": "user", "content": "What is Next.js version 15?"}],
        max_tokens=100
    )
    if not search.choices or not search.choices[0].message:
        print("❌ Invalid response from Perplexity")
        sys.exit(1)
    fact = search.choices[0].message.content
    print(f" Found: {fact[:80]}...")

    # Step 2: Reasoning with GLM-4.7
    print("🧠 Analyzing...")
    response = zai.chat.completions.create(
        model="glm-4.7",
        messages=[
            {"role": "system", "content": "You are a technical analyst."},
            {"role": "user", "content": f"Summarize in one sentence: {fact}"}
        ],
        max_tokens=100
    )
    output = response.choices[0].message.content

    # Validate
    if len(output) > 20:
        print(f"✅ Workflow passed: {output}")
        sys.exit(0)
    else:
        print("❌ Invalid output")
        sys.exit(1)

except OpenAIError as e:
    print(f"❌ API error: {e}")
    sys.exit(1)
except KeyError as e:
    print(f"❌ Invalid response structure: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Workflow failed: {e}")
    raise  # Re-raise to preserve stack trace for unexpected errors
