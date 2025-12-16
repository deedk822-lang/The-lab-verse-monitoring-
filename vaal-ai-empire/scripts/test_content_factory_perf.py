import time
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import importlib

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module that contains the ContentFactory
import services.content_generator as content_module

# Define mocks for external dependencies to avoid actual API calls
class MockAPI:
    def __init__(self, *args, **kwargs):
        # Simulate the I/O or setup cost of a real API client
        time.sleep(0.001)

mock_modules = {
    'api.cohere': MagicMock(CohereAPI=MockAPI),
    'api.groq_api': MagicMock(GroqAPI=MockAPI),
    'api.mistral': MagicMock(MistralAPI=MockAPI),
    'api.huggingface_api': MagicMock(HuggingFaceAPI=MockAPI),
    'api.image_generation': MagicMock(BusinessImageGenerator=MockAPI),
}

class TestContentFactoryPerformance(unittest.TestCase):
    def measure_performance(self, factory_class, runs=100):
        """Helper function to measure instantiation time."""
        start_time = time.perf_counter()
        for _ in range(runs):
            factory_class()
        end_time = time.perf_counter()
        return end_time - start_time

    @patch.dict('sys.modules', mock_modules)
    def test_instantiation_performance_improvement(self):
        """
        Verify that the cached provider initialization is significantly faster
        by comparing the optimized class with a temporarily un-cached version.
        """
        # --- 1. Benchmark the Optimized Version (with @lru_cache) ---
        # Reload the module to ensure the cache is clear before the test
        importlib.reload(content_module)
        OptimizedContentFactory = content_module.ContentFactory

        # The first call will incur the initialization cost
        OptimizedContentFactory()

        # Subsequent calls should be fast
        optimized_time = self.measure_performance(OptimizedContentFactory, runs=100)

        # --- 2. Benchmark the Original (Un-optimized) Version ---
        # Temporarily disable the lru_cache to simulate the original behavior
        with patch('services.content_generator._get_cached_providers.cache_clear'), \
             patch('services.content_generator.lru_cache', lambda maxsize: lambda func: func):

            # We need to reload the module again to apply the patch
            importlib.reload(content_module)
            UnoptimizedContentFactory = content_module.ContentFactory

            unoptimized_time = self.measure_performance(UnoptimizedContentFactory, runs=100)

        # --- 3. Report Results ---
        improvement_factor = unoptimized_time / optimized_time if optimized_time else float('inf')

        print("\n--- Performance Comparison (Corrected) ---")
        print(f"Total time for 100 instantiations (Original):   {unoptimized_time:.6f}s")
        print(f"Total time for 100 instantiations (Optimized):  {optimized_time:.6f}s")
        print(f"Performance Improvement: {improvement_factor:.2f}x faster")
        print("-" * 40)

        # The optimized version should be significantly faster
        self.assertGreater(improvement_factor, 50, "The caching optimization is not effective enough.")

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Running Corrected ContentFactory Performance Benchmark 🚀")
    print("Comparing cached vs. non-cached instantiation time.")
    print("=" * 70)

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestContentFactoryPerformance))
    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    if not result.wasSuccessful():
        print("\n❌ Benchmark failed. The optimization is not effective or the test is flawed.")
        sys.exit(1)

    print("\n✅ Benchmark passed. The optimization is effective and verified.")
