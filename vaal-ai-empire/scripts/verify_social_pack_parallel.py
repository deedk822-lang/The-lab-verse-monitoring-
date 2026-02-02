import logging
import time
import sys
import os
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))

from services.content_generator import ContentFactory

logging.basicConfig(level=logging.INFO)

def benchmark_social_pack():
    print("=" * 60)
    print("BENCHMARK: SOCIAL PACK GENERATION (PARALLEL)")
    print("=" * 60)

    factory = ContentFactory()

    # Mock text generation to take 2 seconds
    original_generate_content = factory.generate_content
    def mocked_generate_content(prompt, max_tokens=500):
        time.sleep(2)
        return {"text": "Post 1 --- Post 2", "provider": "mock", "cost_usd": 0.01, "tokens": 100}
    factory.generate_content = mocked_generate_content

    # Mock image generation to take 3 seconds
    if factory.image_generator:
        original_generate_for_business = factory.image_generator.generate_for_business
        def mocked_generate_for_business(business_type, count=5):
            time.sleep(3)
            return [{"prompt": "mock", "image_url": "mock", "cost_usd": 0.05}] * count
        factory.image_generator.generate_for_business = mocked_generate_for_business

    # In a sequential implementation, it would take 2 + 3 = 5 seconds.
    # In my parallel implementation, it should take max(2, 3) = 3 seconds.

    print("\nGenerating social pack (Parallel)...")
    start = time.perf_counter()
    pack = factory.generate_social_pack("butchery", num_posts=2, num_images=2)
    end = time.perf_counter()

    elapsed = end - start
    print(f"Total Time: {elapsed:.4f}s")

    # Expected time is around 3 seconds, definitely less than 5 seconds.
    if elapsed < 4.5:
        print(f"✓ Parallelization verified: Time {elapsed:.2f}s is less than sequential estimate (5.0s)")
        success = True
    else:
        print(f"⚠️ Parallelization might not be working: Time {elapsed:.2f}s")
        success = False

    return success

if __name__ == "__main__":
    success = benchmark_social_pack()
    sys.exit(0 if success else 1)
