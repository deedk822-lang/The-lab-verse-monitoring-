# vaal-ai-empire/scripts/test_content_factory_perf.py

import time
import sys
import os
from unittest.mock import patch

# --- Path Setup ---
# Add the project root to the Python path to allow importing from 'services'
# This is necessary because the script is in a subdirectory.
def add_project_root_to_path():
    """Add the project root directory to sys.path for module resolution."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added '{project_root}' to sys.path")

# We need to add the path before attempting to import from our project
add_project_root_to_path()
# Now we can import the module we want to test
from vaal_ai_empire.services.content_generator import ContentFactory, get_providers

# --- Mocking ---
# We mock the API clients to prevent them from making real calls or requiring
# API keys during this performance test. This isolates the test to the
# instantiation logic itself.
def mock_api_init(self):
    """A dummy __init__ to replace the real API client initializers."""
    time.sleep(0.05)  # Simulate a small delay for realistic initialization
    pass

@patch('vaal_ai_empire.api.cohere.CohereAPI.__init__', mock_api_init)
@patch('vaal_ai_empire.api.groq_api.GroqAPI.__init__', mock_api_init)
@patch('vaal_ai_empire.api.mistral.MistralAPI.__init__', mock_api_init)
@patch('vaal_ai_empire.api.huggingface_api.HuggingFaceAPI.__init__', mock_api_init)
def run_benchmark():
    """
    Measures and compares the instantiation time of ContentFactory.
    """
    print("=" * 60)
    print("⚡ Bolt: ContentFactory Instantiation Benchmark")
    print("=" * 60)
    print("This test measures the performance gain from caching API providers.")
    print("Mocking API clients to simulate initialization...")

    # --- 1. First Run (Cold Start) ---
    # The first time we call get_providers(), it should be slow because
    # it has to initialize all the (mocked) API clients.
    print("\n--- Testing First Instantiation (Cold Start) ---")
    start_time_first = time.perf_counter()
    factory1 = ContentFactory()
    end_time_first = time.perf_counter()
    first_run_time = end_time_first - start_time_first
    print(f"First instantiation took: {first_run_time:.4f}s (This is expected to be slower)")

    # --- 2. Subsequent Runs (Cached) ---
    # Now that the result of get_providers() is cached by @lru_cache,
    # subsequent instantiations should be extremely fast.
    print("\n--- Testing Subsequent Instantiations (Cached) ---")
    iterations = 100
    start_time_cached = time.perf_counter()
    for _ in range(iterations):
        factory_cached = ContentFactory()
    end_time_cached = time.perf_counter()
    cached_run_total_time = end_time_cached - start_time_cached
    cached_run_avg_time = cached_run_total_time / iterations
    print(f"Ran {iterations} subsequent instantiations in: {cached_run_total_time:.4f}s")
    print(f"Average cached instantiation time: {cached_run_avg_time:.6f}s")

    # --- 3. Verification & Results ---
    print("\n--- Verification & Results ---")
    # Verify that the same provider objects are being reused
    factory2 = ContentFactory()
    assert factory1.providers is factory2.providers, "Providers should be the same object!"
    assert id(factory1.providers) == id(factory2.providers), "Provider object IDs should match!"
    print("✅ Correctness verified: The same cached provider dictionary is used.")

    # Calculate improvement
    # We compare the first run time to the average time of subsequent runs.
    if cached_run_avg_time > 0:
        improvement = (first_run_time - cached_run_avg_time) / first_run_time * 100
        print(f"\nOriginal (uncached) time: {first_run_time:.4f}s")
        print(f"Optimized (cached) time:   {cached_run_avg_time:.6f}s")
        print(f"🚀 Improvement: {improvement:.1f}% faster")
    else:
        improvement = 100 # Effectively infinite improvement
        print("\n🚀 Improvement is virtually instantaneous!")


    if improvement < 90:
        print("\n❌ TEST FAILED: The performance improvement is not significant enough.")
        print("The caching optimization may not be working as expected.")
        return False

    print("\n✅ TEST PASSED: Significant performance improvement confirmed.")
    return True

if __name__ == "__main__":
    # Clear the cache before running to ensure a clean test
    get_providers.cache_clear()
    success = run_benchmark()
    sys.exit(0 if success else 1)