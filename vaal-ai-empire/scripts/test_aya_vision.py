import os
import sys

# Adjust path to import ContentFactory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from services.content_generator import ContentFactory
except ImportError as e:
    print("Error: Could not import ContentFactory. Make sure your environment is set up correctly.")
    print(f"Details: {e}")
    sys.exit(1)

def run_aya_vision_demo():
    """
    Demonstrates the multimodal capabilities of the Aya Vision model through the ContentFactory.
    """
    print("🚀 Running Aya Vision Multimodal Demo...")

    try:
        factory = ContentFactory()
    except Exception as e:
        print(f"❌ Failed to initialize ContentFactory: {e}")
        print("Please ensure you have installed the required dependencies, including the specific 'transformers' version.")
        sys.exit(1)

    if not factory.multimodal_provider:
        print("❌ Aya Vision provider is not available. Please check your installation and logs.")
        sys.exit(1)

    # --- Example 1: Landmark Recognition (Turkish) ---
    print("\n--- Example 1: Landmark Recognition (Turkish) ---")
    messages_landmark = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": "https://media.istockphoto.com/id/458012057/photo/istanbul-turkey.jpg?s=612x612&w=0&k=20&c=qogAOVvkpfUyqLUMr_XJQyq-HkACXyYUSZbKhBlPrxo="},
                {"type": "text", "text": "Bu resimde hangi anıt gösterilmektedir?"},
            ],
        }
    ]

    try:
        result = factory.generate_multimodal_content(messages_landmark)
        print(f"🖼️  Question: {messages_landmark[0]['content'][1]['text']}")
        print(f"🤖 Aya Vision Answer: {result['text']}")
    except Exception as e:
        print(f"❌ An error occurred during landmark recognition demo: {e}")

    # --- Example 2: Text Extraction (Hindi) ---
    print("\n--- Example 2: Text Extraction from Image (Hindi) ---")
    messages_text = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": "https://pbs.twimg.com/media/Fx7YvfQWYAIp6rZ?format=jpg&name=medium"},
                {"type": "text", "text": "चित्र में लिखा पाठ क्या कहता है?"},
            ],
        }
    ]

    try:
        result = factory.generate_multimodal_content(messages_text)
        print(f"🖼️  Question: {messages_text[0]['content'][1]['text']}")
        print(f"🤖 Aya Vision Answer: {result['text']}")
    except Exception as e:
        print(f"❌ An error occurred during text extraction demo: {e}")


if __name__ == "__main__":
    run_aya_vision_demo()
