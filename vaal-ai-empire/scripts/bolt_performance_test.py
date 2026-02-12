import logging
import os
import sys
import time

# Add the project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


# Mock providers to simulate latency
class MockProvider:
    def __init__(self, name, latency=1.0):
        self.name = name
        self.latency = latency

    def generate(self, *args, **kwargs):
        time.sleep(self.latency)
        return {
            "text": f"Mock text from {self.name}",
            "cost_usd": 0.01,
            "usage": {"completion_tokens": 10, "total_tokens": 20},
        }

    def generate_content(self, *args, **kwargs):
        time.sleep(self.latency)
        return {
            "text": f"Mock text from {self.name}",
            "usage": {"output_tokens": 10, "cost_usd": 0.01},
        }

    def generate_for_business(self, *args, **kwargs):
        time.sleep(self.latency)
        return [{"image_url": "mock_url", "cost_usd": 0.01}]


def test_performance():
    print("=" * 60)
    print("BOLT PERFORMANCE VERIFICATION")
    print("=" * 60)

    from services.content_generator import ContentFactory

    factory = ContentFactory()

    # Mock the providers
    mock_text_provider = MockProvider("TextGen", latency=1.0)
    mock_image_gen = MockProvider("ImageGen", latency=1.0)

    factory.providers = {"groq": mock_text_provider}
    factory.image_generator = mock_image_gen

    # Mocking _build_posts_prompt and _parse_posts to avoid logic overhead
    factory._build_posts_prompt = lambda *args: "mock prompt"
    factory._parse_posts = lambda *args: ["post1", "post2"]

    print("\nMeasuring generate_social_pack (Optimized)...")
    start_pack = time.perf_counter()
    pack = factory.generate_social_pack("butchery", num_posts=2, num_images=1)
    end_pack = time.perf_counter()

    optimized_time = end_pack - start_pack
    print(f"Optimized Time: {optimized_time:.4f}s")

    # Sequential time would be ~2.0s
    sequential_time = 2.0
    improvement = ((sequential_time - optimized_time) / sequential_time) * 100
    print(f"Estimated Improvement: {improvement:.1f}% faster than sequential")

    if optimized_time < 1.5:
        print("\n✓ SUCCESS: Parallelization confirmed (Time < 1.5s)")
    else:
        print("\n❌ FAILURE: Still looks sequential")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    test_performance()
