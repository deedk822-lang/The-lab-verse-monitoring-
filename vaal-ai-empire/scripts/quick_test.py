#!/usr/bin/env python3
"""Quick test to verify basic functionality"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test():
    print("🚀 Quick Test Starting...")

    # Test 1: Imports
    try:
        from api.cohere import CohereAPI
        from api.mistral import MistralAPI
        from services.content_generator import ContentFactory
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: API Initialization
    try:
        cohere = CohereAPI()
        mistral = MistralAPI()
        factory = ContentFactory()
        print("✅ All APIs initialized")
    except Exception as e:
        print(f"❌ Init failed: {e}")
        return False

    # Test 3: Content Generation
    try:
        result = cohere.generate_content("Test prompt", max_tokens=50)
        if "text" in result:
            print(f"✅ Content generation works: {result['text'][:50]}...")
        else:
            print("⚠️  Content generation returned unexpected format")
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

    print("\n🎉 QUICK TEST PASSED!")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if quick_test() else 1)
