import logging
import os
import sys
import time
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))

try:
    from services.content_generator import ContentFactory
except ImportError:
    # Handle direct script execution vs module
    sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))
    from services.content_generator import ContentFactory

logging.basicConfig(level=logging.ERROR)

def benchmark_social_pack():
    print("=" * 60)
    print("PERFORMANCE BENCHMARK: SOCIAL PACK GENERATION")
    print("=" * 60)

    factory = ContentFactory()

    # Mock generate_content to simulate delay
    original_generate_content = factory.generate_content
    def mocked_generate_content(prompt, max_tokens=500):
        print("Starting text generation (simulated 2s delay)...")
        time.sleep(2)
        return {
            "text": "Post 1 --- Post 2",
            "provider": "mock",
            "cost_usd": 0.01,
            "tokens": 100
        }
    factory.generate_content = mocked_generate_content

    # Mock image_generator.generate_for_business to simulate delay
    if factory.image_generator:
        original_generate_for_business = factory.image_generator.generate_for_business
        def mocked_generate_for_business(business_type, count=5):
            print("Starting image generation (simulated 2s delay)...")
            time.sleep(2)
            return [{"image_url": "mock_url", "cost_usd": 0.05}] * count
        factory.image_generator.generate_for_business = mocked_generate_for_business
    else:
        print("Warning: image_generator not found, creating a mock one.")
        factory.image_generator = MagicMock()
        def mocked_generate_for_business(business_type, count=5):
            print("Starting image generation (simulated 2s delay)...")
            time.sleep(2)
            return [{"image_url": "mock_url", "cost_usd": 0.05}] * count
        factory.image_generator.generate_for_business = mocked_generate_for_business

    # Measure performance
    print("\nRunning generate_social_pack...")
    start_time = time.perf_counter()
    result = factory.generate_social_pack("butchery", num_posts=2, num_images=2)
    end_time = time.perf_counter()

    total_time = end_time - start_time
    print(f"\nTotal Time: {total_time:.4f}s")

    # In sequential mode, it should be at least 4 seconds (2s for text + 2s for images)
    # In parallel mode, it should be around 2 seconds.

    if total_time >= 3.8:
        print("Current mode: SEQUENTIAL (Detected)")
    elif total_time >= 1.8:
        print("Current mode: PARALLEL (Detected)")
    else:
        print("Current mode: UNKNOWN (Too fast)")

    return total_time

if __name__ == "__main__":
    benchmark_social_pack()
