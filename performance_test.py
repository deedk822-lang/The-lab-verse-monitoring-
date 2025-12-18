
import time
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Dynamically add the project root to the Python path
# This allows us to import modules from the 'vaal-ai-empire' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaal-ai-empire')))

from services.content_generator import content_factory, ContentFactory


def benchmark_operation(func, iterations=1000):
    """Benchmark the time it takes to execute a function."""
    start = time.perf_counter()
    for _ in range(iterations):
        instance = func()
    end = time.perf_counter()
    return end - start

class TestSingletonPerformance(unittest.TestCase):
    """Performance tests for the ContentFactory singleton optimization."""

    @patch('services.content_generator._get_cached_providers')
    def test_singleton_performance_improvement(self, mock_get_providers):
        """
        Verify that using the singleton is faster than repeated instantiation.
        """
        # Mock the expensive provider initialization to isolate the test
        # to the performance of object creation itself.
        mock_get_providers.return_value = ({}, MagicMock())

        print("\n" + "="*60)
        print("⚡ Bolt: ContentFactory Singleton Performance Benchmark ⚡")
        print("="*60)
        print("Objective: Verify that using a shared singleton instance is")
        print("           faster than creating a new instance every time.")
        print("-" * 60)

        iterations = 5000

        # --- Benchmark: Unoptimized (repeated instantiation) ---
        print(f"Running Unoptimized Benchmark ({iterations} instantiations)...")
        unoptimized_time = benchmark_operation(ContentFactory, iterations)
        print(f"Unoptimized Time: {unoptimized_time:.4f}s")
        self.assertGreater(unoptimized_time, 0)

        # --- Benchmark: Optimized (accessing singleton) ---
        def access_singleton():
            # Simulate accessing the already-created singleton instance
            return content_factory

        print(f"Running Optimized Benchmark ({iterations} singleton accesses)...")
        optimized_time = benchmark_operation(access_singleton, iterations)
        print(f"Optimized Time:   {optimized_time:.4f}s")

        # --- Analysis ---
        print("-" * 60)
        try:
            improvement = ((unoptimized_time - optimized_time) / unoptimized_time) * 100
            print(f"✅ Performance Improvement: {improvement:.1f}%")
            self.assertGreater(improvement, 50, "Expected a significant performance improvement.")
        except ZeroDivisionError:
            self.fail("Unoptimized time was zero, benchmark failed.")

        print("="*60)
        print("Conclusion: The singleton pattern significantly reduces overhead.")

if __name__ == '__main__':
    unittest.main()
