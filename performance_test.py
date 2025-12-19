 bolt/parallelize-daily-automation-8919749710849742159


 bolt/cache-hf-model-loading-6086113376814306475
import timeit
import sys

# Add the project directory to the Python path
sys.path.insert(0, 'vaal-ai-empire')

# To benchmark the original, we need to simulate the old code
from unittest.mock import patch
from sentence_transformers import SentenceTransformer

# Original (simulated) implementation
class OriginalHuggingFaceLab:
    def __init__(self):
        try:
            self.seo_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            self.seo_model = None

    def optimize_keywords(self, keywords: list):
        if not self.seo_model: return 0
        embeddings = self.seo_model.encode(keywords)
        return len(embeddings)

# Optimized implementation
from src.core.hf_lab import HuggingFaceLab as OptimizedHuggingFaceLab

def benchmark():
    """Compare original vs optimized performance."""
    print("=" * 60)
    print("⚡ BOLT: PERFORMANCE COMPARISON TEST")
    print("=" * 60)

    # --- Correctness Check ---
    # We need to install dependencies to run this check
    try:
        original_instance = OriginalHuggingFaceLab()
        optimized_instance = OptimizedHuggingFaceLab()

        test_keywords = ["python", "performance", "optimization"]
        original_result = original_instance.optimize_keywords(test_keywords)
        optimized_result = optimized_instance.optimize_keywords(test_keywords)

        assert original_result == optimized_result, f"Results do not match! Original: {original_result}, Optimized: {optimized_result}"
        print("✅ Correctness verified: Results match")
    except ImportError as e:
        print(f"⚠️ Skipping correctness check: Dependency not found ({e}). Please run 'pip install sentence-transformers'.")
    except Exception as e:
        print(f"❌ Correctness check failed: {e}")
        return False

    # --- Speed Benchmark ---
    iterations = 10  # Instantiation is slow, so we use fewer iterations

    # Measure original
    original_setup = "from __main__ import OriginalHuggingFaceLab"
    original_code = "OriginalHuggingFaceLab()"
    original_time = timeit.timeit(original_code, setup=original_setup, number=iterations)

    # Measure optimized
    optimized_setup = "from src.core.hf_lab import HuggingFaceLab as OptimizedHuggingFaceLab"
    optimized_code = "OptimizedHuggingFaceLab()"
    optimized_time = timeit.timeit(optimized_code, setup=optimized_setup, number=iterations)

    # The first run of the optimized version will be slow due to model loading.
    # We run it once to cache the model, then benchmark subsequent runs.
    print("\nCaching optimized model...")
    first_run_setup = "from src.core.hf_lab import HuggingFaceLab as OptimizedHuggingFaceLab; OptimizedHuggingFaceLab()"
    cached_optimized_time = timeit.timeit(optimized_code, setup=first_run_setup, number=iterations)

    print(f"\n--- Benchmark Results ({iterations} instantiations) ---")
    print(f"Original Total Time:      {original_time:.4f}s")
    print(f"Optimized (First Run):    {optimized_time:.4f}s (includes one-time model load)")
    print(f"Optimized (Subsequent):   {cached_optimized_time:.4f}s (uses cached model)")

    try:
        improvement = ((original_time - cached_optimized_time) / original_time) * 100
        print(f"\nImprovement (Subsequent): {improvement:.1f}% faster")

        if improvement > 10:
            print("✅ SIGNIFICANT IMPROVEMENT DETECTED")
        elif improvement > 0:
            print("✅ Minor improvement")
        else:
            print("⚠️ NO IMPROVEMENT - Optimization may not be effective")
        return improvement > 0
    except ZeroDivisionError:
        print("⚠️ Could not calculate improvement (division by zero).")
        return False


if __name__ == "__main__":
    success = benchmark()

 vercel/enable-vercel-speed-insights-o-6em3bz
import time
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure the script can find the vaal-ai-empire modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaal-ai-empire')))

from scripts.daily_automation import DailyAutomation

# Mock data for clients
MOCK_CLIENTS = [
    {"id": f"client_{i}", "name": f"Client {i}", "business_type": "butchery", "language": "afrikaans"}
    for i in range(20)
]

def benchmark_sequential(automation_instance):
    """Benchmarks the original sequential method."""
    print("\n--- Benchmarking OLD Sequential Method ---")
    start_time = time.perf_counter()

    for client in MOCK_CLIENTS:
        automation_instance._generate_for_client(client)

    end_time = time.perf_counter()
    return end_time - start_time

def benchmark_parallel(automation_instance):
    """Benchmarks the new parallelized method."""
    print("\n--- Benchmarking NEW Parallel Method ---")
    start_time = time.perf_counter()

    with patch.object(automation_instance.db, 'get_active_clients', return_value=MOCK_CLIENTS):
        automation_instance.generate_content_for_all_clients()

    end_time = time.perf_counter()
    return end_time - start_time

@patch('scripts.daily_automation.ContentScheduler')
@patch('scripts.daily_automation.ContentFactory')
@patch('scripts.daily_automation.Database')
def test_optimization(MockDatabase, MockFactory, MockScheduler):
    """Compare original vs optimized performance."""
    print("=" * 60)
    print("⚡ Bolt: Performance Comparison Test ⚡")
    print("=" * 60)
    print(f"Simulating content generation for {len(MOCK_CLIENTS)} clients...")

    # Mock the dependencies to isolate the concurrency logic
    mock_db_instance = MockDatabase.return_value
    mock_factory_instance = MockFactory.return_value
    mock_scheduler_instance = MockScheduler.return_value

    # Simulate a network delay in content generation
    def fake_generation(business_type, language):
        time.sleep(0.1)  # Simulate 100ms I/O delay
        return {"posts": ["post1", "post2"]}

    mock_factory_instance.generate_social_pack.side_effect = fake_generation
    mock_scheduler_instance.schedule_pack.return_value = None

    # Create an instance of the automation class with mocked dependencies
    automation = DailyAutomation()
    automation.db = mock_db_instance
    automation.factory = mock_factory_instance
    automation.scheduler = mock_scheduler_instance

    # --- Benchmark Sequential ---
    sequential_time = benchmark_sequential(automation)

    # --- Benchmark Parallel ---
    parallel_time = benchmark_parallel(automation)

    # --- Report Results ---
    improvement = ((sequential_time - parallel_time) / sequential_time) * 100

    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("-" * 60)
    print(f"Sequential Time: {sequential_time:.4f}s")
    print(f"Parallel Time:   {parallel_time:.4f}s")
    print("-" * 60)
    print(f"🚀 Improvement: {improvement:.2f}% faster")
    print("=" * 60)

    if improvement > 50:
        print("✅ SUCCESS: Significant performance improvement verified!")
        return True
    else:
        print("⚠️ FAILURE: No significant improvement. Optimization may not be effective.")
        return False

if __name__ == "__main__":
    success = test_optimization()
 main
    sys.exit(0 if success else 1)
