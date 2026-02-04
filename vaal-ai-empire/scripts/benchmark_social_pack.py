
import sys
import os
import time
import logging
import concurrent.futures

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))

from services.content_generator import ContentFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def benchmark_social_pack():
    print("=" * 60)
    print("BENCHMARKING generate_social_pack")
    print("=" * 60)

    factory = ContentFactory()

    # Mock generate_content and image_generator.generate_for_business
    # to simulate network latency

    original_generate_content = factory.generate_content
    def mocked_generate_content(prompt, max_tokens=500):
        logger.info("Simulating content generation (2s)...")
        time.sleep(2)
        return {
            "text": "Post 1 --- Post 2 --- Post 3",
            "provider": "mock",
            "cost_usd": 0.01,
            "tokens": 100
        }

    factory.generate_content = mocked_generate_content

    if factory.image_generator:
        original_generate_for_business = factory.image_generator.generate_for_business
        def mocked_generate_for_business(business_type, count=5):
            logger.info("Simulating image generation (3s)...")
            time.sleep(3)
            return [{"image_url": "mock_url", "cost_usd": 0.05}] * count

        factory.image_generator.generate_for_business = mocked_generate_for_business

    # Measure current sequential performance
    print("\nMeasuring Sequential Performance...")
    start_time = time.perf_counter()
    factory.generate_social_pack("butchery", num_posts=3, num_images=2)
    sequential_time = time.perf_counter() - start_time
    print(f"Sequential Time: {sequential_time:.4f}s")

    # Expected time is ~5s (2s for posts + 3s for images)

    return sequential_time

if __name__ == "__main__":
    benchmark_social_pack()
