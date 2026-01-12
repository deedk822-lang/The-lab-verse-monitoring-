#!/usr/bin/env python3
"""
test_brain.py - Two-Stage AI Workflow Test
Tests Perplexity (research) → Z.ai (reasoning) pipeline
"""

import os
import sys
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def validate_response(client_response, client_name):
    """Validate API response structure"""
    if not client_response:
        print(f"❌ {client_name}: Empty response")
        return None

    if not hasattr(client_response, 'choices') or not client_response.choices:
        print(f"❌ {client_name}: No choices in response")
        return None

    if not hasattr(client_response.choices[0], 'message'):
        print(f"❌ {client_name}: No message in response")
        return None

    content = client_response.choices[0].message.content

    if not content or not isinstance(content, str):
        print(f"❌ {client_name}: Invalid content")
        return None

    return content


def validate_output(text, min_length=20):
    """Validate final output quality"""
    if not text:
        return False, "Output is empty"

    text = text.strip()

    if len(text) < min_length:
        return False, f"Output too short ({len(text)} chars, need {min_length}+)"

    # Check it's not just whitespace or error message
    if not text or text.isspace():
        return False, "Output is only whitespace"

    # Check for common error patterns
    error_keywords = ["error", "failed", "invalid", "exception", "traceback"]
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in error_keywords):
        return False, f"Output contains error indicators: {text[:100]}..."

    # Basic structure check - should have some substance
    word_count = len(text.split())
    if word_count < 5:
        return False, f"Output too simple ({word_count} words)"

    return True, "Valid"


def main():
    print("🧪 Testing AI Workflow: Perplexity → Z.ai")
    print("=" * 50)

    # Initialize clients
    try:
        pplx = OpenAI(
            api_key=os.getenv("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai"
        )

        zai = OpenAI(
            api_key=os.getenv("ZAI_API_KEY"),
            base_url="https://api.z.ai/api/paas/v4/"
        )
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        sys.exit(1)

    # Step 1: Research with Perplexity
    print("🔍 Researching with Perplexity Sonar Pro...")
    try:
        search = pplx.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": "What is the latest stable Python version as of 2025?"}
            ],
            max_tokens=200
        )

        fact = validate_response(search, "Perplexity")
        if not fact:
            sys.exit(1)

        print(f"✅ Research complete: {fact[:100]}...")

    except Exception as e:
        print(f"❌ Perplexity research failed: {e}")
        sys.exit(1)

    # Step 2: Reasoning with Z.ai
    print("\n🧠 Analyzing with Z.ai GLM-4.7...")
    try:
        response = zai.chat.completions.create(
            model="glm-4.7",
            messages=[
                {"role": "system", "content": "You are a technical analyst. Provide clear, concise summaries."},
                {"role": "user", "content": f"Summarize this information in one sentence: {fact}"}
            ],
            max_tokens=100
        )

        output = validate_response(response, "Z.ai")
        if not output:
            sys.exit(1)

        print(f"✅ Analysis complete: {output}")

    except Exception as e:
        print(f"❌ Z.ai analysis failed: {e}")
        sys.exit(1)

    # Step 3: Validate final output
    print("\n🔍 Validating output quality...")
    is_valid, validation_msg = validate_output(output)

    if is_valid:
        print(f"✅ Workflow passed: {validation_msg}")
        print(f"\n📊 Final Output:\n{output}")
        sys.exit(0)
    else:
        print(f"❌ Validation failed: {validation_msg}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
