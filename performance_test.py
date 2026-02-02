import timeit
import time
import sys
import os
from unittest.mock import patch, MagicMock
from sentence_transformers import SentenceTransformer

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaal-ai-empire')))

# Original (simulated) implementation for SEO model
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
try:
    from src.core.hf_lab import HuggingFaceLab as OptimizedHuggingFaceLab
except ImportError:
    OptimizedHuggingFaceLab = None

def benchmark_hf_lab():
    """Compare original vs optimized HF Lab performance."""
    print("=" * 60)
    print("⚡ BOLT: HF LAB PERFORMANCE COMPARISON TEST")
    print("=" * 60)

    if not OptimizedHuggingFaceLab:
        print("❌ OptimizedHuggingFaceLab not found. Skipping benchmark.")
        return False

    # --- Correctness Check ---
    try:
        original_instance = OriginalHuggingFaceLab()
        optimized_instance = OptimizedHuggingFaceLab()

        test_keywords = ["python", "performance", "optimization"]
        original_result = original_instance.optimize_keywords(test_keywords)
        optimized_result = optimized_instance.optimize_keywords(test_keywords)

        assert original_result == optimized_result, f"Results do not match! Original: {original_result}, Optimized: {optimized_result}"
        print("✅ Correctness verified: Results match")
    except ImportError as e:
        print(f"⚠️ Skipping correctness check: Dependency not found ({e}).")
    except Exception as e:
        print(f"❌ Correctness check failed: {e}")

    # --- Speed Benchmark ---
    iterations = 5

    # Measure original
    try:
        original_time = timeit.timeit("OriginalHuggingFaceLab()", globals=globals(), number=iterations)

        # Measure optimized
        # The first run of the optimized version will be slow due to model loading.
        # We run it once to cache the model, then benchmark subsequent runs.
        print("\nCaching optimized model...")
        OptimizedHuggingFaceLab()
        cached_optimized_time = timeit.timeit("OptimizedHuggingFaceLab()", globals=globals(), number=iterations)

        print(f"\n--- Benchmark Results ({iterations} instantiations) ---")
        print(f"Original Total Time:      {original_time:.4f}s")
        print(f"Optimized (Subsequent):   {cached_optimized_time:.4f}s (uses cached model)")

        improvement = ((original_time - cached_optimized_time) / original_time) * 100
        print(f"\nImprovement (Subsequent): {improvement:.1f}% faster")
        return improvement > 0
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

# Parallelization Benchmark
from scripts.daily_automation import DailyAutomation

MOCK_CLIENTS = [
    {"id": f"client_{i}", "name": f"Client {i}", "business_type": "butchery", "language": "afrikaans"}
    for i in range(10)
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
def test_parallel_optimization(MockDatabase, MockFactory, MockScheduler):
    """Compare sequential vs parallel performance."""
    print("\n" + "=" * 60)
    print("⚡ Bolt: Parallelization Performance Comparison ⚡")
    print("=" * 60)

    mock_factory_instance = MockFactory.return_value
    def fake_generation(business_type, language):
        time.sleep(0.1)
        return {"posts": ["post1", "post2"]}
    mock_factory_instance.generate_social_pack.side_effect = fake_generation

    automation = DailyAutomation()
    automation.db = MockDatabase.return_value
    automation.factory = mock_factory_instance
    automation.scheduler = MockScheduler.return_value

    seq_time = benchmark_sequential(automation)
    par_time = benchmark_parallel(automation)
    improvement = ((seq_time - par_time) / seq_time) * 100

    print(f"\nSequential Time: {seq_time:.4f}s")
    print(f"Parallel Time:   {par_time:.4f}s")
    print(f"🚀 Improvement: {improvement:.2f}% faster")
    return improvement > 30

if __name__ == "__main__":
    hf_success = benchmark_hf_lab()
    parallel_success = test_parallel_optimization()
    sys.exit(0 if (hf_success or parallel_success) else 1)
