# vaal-ai-empire/scripts/test_content_factory_perf.py
import time
import sys
import os
import unittest
from unittest.mock import patch

# Add the project directory to the path to allow direct import.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.content_generator import ContentFactory as OptimizedContentFactory
from services.content_generator import _get_providers

def benchmark_instantiation(cls, iterations=100):
    """Benchmark the instantiation of a class over multiple iterations."""
    start = time.perf_counter()
    for _ in range(iterations):
        instance = cls()
    end = time.perf_counter()
    return end - start

def test_optimization():
    """Verify the performance of the optimized ContentFactory."""
    print("=" * 60)
    print("⚡ Bolt: Performance Verification Test ⚡")
    print("=" * 60)
    print("Target: Caching the API provider initialization in ContentFactory.")
    print("Method: Verifying that subsequent instantiations are extremely fast.")
    print("-" * 60)

    iterations = 100

    # --- Benchmark Optimized ---
    # Clear the cache before the test for a fair measurement
    _get_providers.cache_clear()

    print(f"Benchmarking OptimizedContentFactory ({iterations} iterations)...")

    # First call will be slower as it populates the cache.
    first_call_start = time.perf_counter()
    OptimizedContentFactory()
    first_call_end = time.perf_counter()
    first_call_time = first_call_end - first_call_start
    print(f"First instantiation time (cache miss): {first_call_time:.4f}s")

    # Subsequent calls will be much faster.
    subsequent_time = benchmark_instantiation(OptimizedContentFactory, iterations)
    print(f"Subsequent {iterations} instantiations total time (cache hit): {subsequent_time:.4f}s")

    # --- Report Results ---
    # The time for subsequent calls should be negligible
    is_fast = subsequent_time < 0.01

    print("-" * 60)
    print(f"Subsequent Instantiation Time: {subsequent_time:.4f}s")
    print(f"Is subsequent time negligible (< 0.01s)? {'Yes' if is_fast else 'No'}")
    print("=" * 60)

    if is_fast:
        print("✅ SUCCESS: Significant performance improvement verified.")
        return True
    else:
        print("⚠️  WARNING: Optimization did not yield significant improvement.")
        return False

if __name__ == "__main__":
    # Mock the API clients to prevent real API calls or dependency errors during the test
    with patch.dict(sys.modules, {
        'api.cohere': unittest.mock.MagicMock(),
        'api.groq_api': unittest.mock.MagicMock(),
        'api.mistral': unittest.mock.MagicMock(),
        'api.huggingface_api': unittest.mock.MagicMock(),
        'api.image_generation': unittest.mock.MagicMock(),
    }):
        success = test_optimization()
        sys.exit(0 if success else 1)
