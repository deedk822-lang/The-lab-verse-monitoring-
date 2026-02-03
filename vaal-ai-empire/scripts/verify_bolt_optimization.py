import time
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BoltVerifier")

def benchmark_social_pack_parallel():
    from services.content_generator import ContentFactory
    from api.image_generation import BusinessImageGenerator

    # 1. Mock text generation
    def mock_generate_content(prompt, max_tokens=500):
        time.sleep(1) # Simulate 1s for text generation
        return {"text": "Post 1 --- Post 2 --- Post 3", "provider": "mock", "cost_usd": 0.01, "tokens": 100}

    # 2. Setup real BusinessImageGenerator but mock the individual image generation
    image_gen = BusinessImageGenerator()

    def mock_generate_single(prompt, style="professional", provider="auto"):
        time.sleep(0.5) # Simulate 0.5s per image
        return {"image_url": "http://example.com/img.png", "provider": "mock", "cost_usd": 0.01}

    image_gen.generator.generate = mock_generate_single

    factory = ContentFactory()
    factory.generate_content = mock_generate_content
    factory.image_generator = image_gen

    logger.info("Starting Parallel Social Pack Generation Benchmark...")
    start_time = time.perf_counter()
    pack = factory.generate_social_pack("butchery", num_posts=3, num_images=5)
    end_time = time.perf_counter()

    duration = end_time - start_time
    logger.info(f"Parallel duration: {duration:.2f} seconds")

    return duration

def benchmark_social_pack_sequential():
    # We simulate sequential by mocking the parallelized methods back to sequential
    from services.content_generator import ContentFactory
    from api.image_generation import BusinessImageGenerator

    factory = ContentFactory()

    def mock_generate_content(prompt, max_tokens=500):
        time.sleep(1) # Simulate 1s for text generation
        return {"text": "Post 1 --- Post 2 --- Post 3", "provider": "mock", "cost_usd": 0.01, "tokens": 100}

    def mock_generate_for_business(business_type, count=5):
        # Force sequential
        results = []
        for i in range(count):
            time.sleep(0.5)
            results.append({"image_url": "http://example.com/img.png", "cost_usd": 0.01})
        return results

    # Re-implement sequential generate_social_pack logic for comparison
    def sequential_generate_social_pack(self, business_type, language="afrikaans", num_posts=3, num_images=5):
        posts_prompt = self._build_posts_prompt(business_type, language, num_posts)
        posts_result = self.generate_content(posts_prompt, max_tokens=2000)
        posts = self._parse_posts(posts_result["text"], num_posts)
        images = self.image_generator.generate_for_business(business_type, count=num_images)
        return {"posts": posts, "images": images}

    factory.generate_content = mock_generate_content
    factory.image_generator = MagicMock()
    factory.image_generator.generate_for_business = mock_generate_for_business

    logger.info("Starting Sequential Social Pack Generation Benchmark (simulated)...")
    start_time = time.perf_counter()
    pack = sequential_generate_social_pack(factory, "butchery")
    end_time = time.perf_counter()

    duration = end_time - start_time
    logger.info(f"Sequential duration: {duration:.2f} seconds")

    return duration

def run_verification():
    print("\n" + "="*60)
    print("⚡ BOLT PERFORMANCE VERIFICATION ⚡")
    print("="*60)

    mock_modules = {
        'api.cohere': MagicMock(),
        'api.groq_api': MagicMock(),
        'api.mistral': MagicMock(),
        'api.huggingface_api': MagicMock(),
        'api.kimi': MagicMock(),
        'api.aya_vision': MagicMock(),
    }

    with patch.dict('sys.modules', mock_modules):
        seq_time = benchmark_social_pack_sequential()
        par_time = benchmark_social_pack_parallel()

        improvement = ((seq_time - par_time) / seq_time) * 100

        print("\n" + "-"*60)
        print(f"Sequential Duration: {seq_time:.2f}s")
        print(f"Parallel Duration:   {par_time:.2f}s")
        print(f"Speedup:             {improvement:.1f}%")
        print("-"*60)

        if improvement >= 50:
            print("✅ SUCCESS: Performance optimization is highly effective!")
            return True
        else:
            print("⚠️ WARNING: Performance improvement below expected threshold.")
            return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
