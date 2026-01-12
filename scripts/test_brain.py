import os
import sys
import time

try:
    import anthropic
except ImportError:
    print("❌ Missing dependency. Run: pip install anthropic")
    sys.exit(1)

def test_brain_function():
    print("🧠 Testing Anthropic Reasoning Capability...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    start_time = time.time()
    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307", # Use Haiku for fast/cheap testing
            max_tokens=20,
            messages=[
                {"role": "user", "content": "Return the JSON object {'status': 'online'}. Do not say anything else."}
            ]
        )

        duration = round((time.time() - start_time) * 1000, 2)
        response = message.content[0].text

        print(f"✅ Brain Response Received in {duration}ms")
        print(f"📄 Output: {response}")

        if "online" in response:
            print("🚀 Cognitive Check Passed.")
            sys.exit(0)
        else:
            print("⚠️ Response format unexpected.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Brain Failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_brain_function()
