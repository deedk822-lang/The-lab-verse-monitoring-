
import time
import unittest
from unittest.mock import patch, MagicMock
import logging
from datetime import datetime
import importlib

# Configure logging to avoid noisy output during tests
logging.basicConfig(level=logging.ERROR)

# --- Import modules with hyphens using importlib ---
content_generator_module = importlib.import_module("vaal-ai-empire.services.content_generator")
ContentFactory = content_generator_module.ContentFactory
image_generation_module = importlib.import_module("vaal-ai-empire.api.image_generation")
BusinessImageGenerator = image_generation_module.BusinessImageGenerator

# --- Original (un-optimized) implementation for baseline comparison ---
# This class simulates the state of the code BEFORE the optimization.
class OriginalContentFactory:
    def __init__(self, db=None):
        self.db = db
        # Mock dependencies directly for the baseline test
        self.image_generator = MagicMock()
        # Ensure the mock has the necessary method
        self.image_generator.generate_for_business = MagicMock()

    def generate_content(self, prompt: str, max_tokens: int = 500) -> dict:
        # This will be patched during the test to simulate a network call
        pass

    def _build_posts_prompt(self, business_type: str, language: str, num_posts: int) -> str:
        # Simplified version for testing purposes
        return f"Generate {num_posts} posts for {business_type} in {language}"

    def _parse_posts(self, text: str, expected_count: int) -> list[str]:
        return [f"Post {i+1}" for i in range(expected_count)]

    def _create_placeholder_images(self, count: int) -> list[dict]:
        return [{"image_url": f"placeholder_{i+1}.png"} for i in range(count)]

    def generate_social_pack(self, business_type: str, language: str = "afrikaans",
                            num_posts: int = 10, num_images: int = 5) -> dict:
        """
        The ORIGINAL sequential implementation.
        """
        logging.info(f"Generating social pack for {business_type} ({language})")

        posts_prompt = self._build_posts_prompt(business_type, language, num_posts)
        # 1. First network call (blocking)
        posts_result = self.generate_content(posts_prompt, max_tokens=2000)
        posts = self._parse_posts(posts_result["text"], num_posts)

        images = []
        if self.image_generator:
            try:
                # 2. Second network call (blocking)
                image_results = self.image_generator.generate_for_business(business_type, count=num_images)
                images = image_results
            except Exception as e:
                images = self._create_placeholder_images(num_images)
        else:
            images = self._create_placeholder_images(num_images)

        total_cost = posts_result.get("cost_usd", 0.0)
        total_cost += sum(img.get("cost_usd", 0.0) for img in images)

        pack = {"posts": posts, "images": images, "metadata": {"business_type": business_type, "language": language, "generated_at": datetime.now().isoformat(), "provider": posts_result.get("provider"), "cost_usd": total_cost, "tokens_used": posts_result.get("tokens", 0)}}

        return pack

class TestPerformanceOptimization(unittest.TestCase):

    @patch.object(ContentFactory, 'generate_content')
    @patch.object(BusinessImageGenerator, 'generate_for_business')
    def test_parallelization_speedup(self, mock_generate_images, mock_generate_text):
        """
        Verify that the parallel implementation is faster than the sequential one.
        """
        # --- Mock Configuration ---
        # Simulate network latency for both text and image generation
        TEXT_GENERATION_LATENCY = 0.5  # seconds
        IMAGE_GENERATION_LATENCY = 0.8  # seconds

        def text_side_effect(*args, **kwargs):
            time.sleep(TEXT_GENERATION_LATENCY)
            return {"text": "mocked text", "cost_usd": 0.01, "provider": "mock_text"}

        def image_side_effect(*args, **kwargs):
            time.sleep(IMAGE_GENERATION_LATENCY)
            return [{"image_url": "mocked_image.png", "cost_usd": 0.05}]

        # Assign mocks to the optimized factory's dependencies
        mock_generate_text.side_effect = text_side_effect
        mock_generate_images.side_effect = image_side_effect

        # --- Benchmark Original (Sequential) Implementation ---
        original_factory = OriginalContentFactory()

        # Patch the original factory's methods for a fair comparison
        with patch.object(original_factory, 'generate_content', side_effect=text_side_effect), \
             patch.object(original_factory.image_generator, 'generate_for_business', side_effect=image_side_effect):

            start_time_original = time.perf_counter()
            original_result = original_factory.generate_social_pack("butchery")
            end_time_original = time.perf_counter()
            original_duration = end_time_original - start_time_original

        # --- Benchmark New (Parallel) Implementation ---
        # We need to mock the providers cache to inject our mocked image generator
        with patch.object(content_generator_module, '_get_cached_providers') as mock_get_providers:
            mock_image_gen = MagicMock()
            mock_image_gen.generate_for_business = mock_generate_images
            mock_get_providers.return_value = ({}, mock_image_gen, None)

            optimized_factory = ContentFactory()

            start_time_optimized = time.perf_counter()
            optimized_result = optimized_factory.generate_social_pack("butchery")
            end_time_optimized = time.perf_counter()
            optimized_duration = end_time_optimized - start_time_optimized

        # --- Verification ---
        print("\n" + "="*60)
        print("⚡ BOLT: PERFORMANCE BENCHMARK RESULTS ⚡")
        print("="*60)
        print(f"Original (Sequential) Time: {original_duration:.4f} seconds")
        print(f"Optimized (Parallel) Time:  {optimized_duration:.4f} seconds")
        print("-"*60)

        expected_original_duration = TEXT_GENERATION_LATENCY + IMAGE_GENERATION_LATENCY
        print(f"Expected Sequential Time:   ~{expected_original_duration:.4f}s (text + image latency)")

        expected_optimized_duration = max(TEXT_GENERATION_LATENCY, IMAGE_GENERATION_LATENCY)
        print(f"Expected Parallel Time:     ~{expected_optimized_duration:.4f}s (max(text, image) latency)")
        print("-"*60)

        # Assert correctness: the structure of the output should be the same
        self.assertEqual(len(original_result['posts']), len(optimized_result['posts']))
        # The number of images should be the same, even if mock details differ
        self.assertEqual(len(original_result['images']), len(optimized_result['images']))
        print("✅ Correctness: Output structure matches between versions.")

        # Assert performance: the optimized version must be faster
        self.assertLess(optimized_duration, original_duration)
        improvement = ((original_duration - optimized_duration) / original_duration) * 100
        print(f"🚀 Performance Improvement:  {improvement:.2f}% faster")
        print("="*60)

        # The optimized duration should be close to the longest single operation, not the sum
        self.assertLess(optimized_duration, expected_original_duration * 0.9) # Allow for some overhead
        self.assertGreater(optimized_duration, expected_optimized_duration * 0.9)


if __name__ == '__main__':
    # To run this test: python performance_test.py
    unittest.main()
