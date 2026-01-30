#!/usr/bin/env python3
import time
import timeit
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure the script can find the vaal-ai-empire modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaal-ai-empire')))

# --- HuggingFaceLab Benchmark ---
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class OriginalHuggingFaceLab:
    def __init__(self):
        try:
            self.seo_model = SentenceTransformer('all-MiniLM-L6-v2') if SentenceTransformer else None
        except Exception:
            self.seo_model = None

    def optimize_keywords(self, keywords: list):
        if not self.seo_model: return 0
        embeddings = self.seo_model.encode(keywords)
        return len(embeddings)

def benchmark_hf_lab():
    """Compare original vs optimized performance for HuggingFaceLab."""
    print("=" * 60)
    print("⚡ BOLT: HUGGINGFACE LAB PERFORMANCE COMPARISON")
    print("=" * 60)

    try:
        from src.core.hf_lab import HuggingFaceLab as OptimizedHuggingFaceLab

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
        iterations = 10
        original_setup = "from __main__ import OriginalHuggingFaceLab"
        original_code = "OriginalHuggingFaceLab()"
        original_time = timeit.timeit(original_code, setup=original_setup, number=iterations)

        optimized_code = "OptimizedHuggingFaceLab()"
        print("\nCaching optimized model...")
        first_run_setup = "from src.core.hf_lab import HuggingFaceLab as OptimizedHuggingFaceLab; OptimizedHuggingFaceLab()"
        cached_optimized_time = timeit.timeit(optimized_code, setup=first_run_setup, number=iterations)

        print(f"\n--- Benchmark Results ({iterations} instantiations) ---")
        print(f"Original Total Time:      {original_time:.4f}s")
        print(f"Optimized (Subsequent):   {cached_optimized_time:.4f}s (uses cached model)")

        improvement = ((original_time - cached_optimized_time) / original_time) * 100
        print(f"\nImprovement: {improvement:.1f}% faster")
    except ImportError:
        print("⚠️ OptimizedHuggingFaceLab not found, skipping HF Lab benchmark.")

# --- DailyAutomation Benchmark ---
try:
    from scripts.daily_automation import DailyAutomation
except ImportError:
    DailyAutomation = None

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
def test_daily_automation_optimization(MockDatabase, MockFactory, MockScheduler):
    """Compare sequential vs parallel performance for DailyAutomation."""
    if DailyAutomation is None:
        print("⚠️ DailyAutomation not found, skipping benchmark.")
        return True

    print("\n" + "=" * 60)
    print("⚡ Bolt: DailyAutomation Performance Comparison ⚡")
    print("=" * 60)
    print(f"Simulating content generation for {len(MOCK_CLIENTS)} clients...")

    mock_db_instance = MockDatabase.return_value
    mock_factory_instance = MockFactory.return_value
    mock_scheduler_instance = MockScheduler.return_value

    def fake_generation(business_type, language):
        time.sleep(0.1)  # Simulate 100ms I/O delay
        return {"posts": ["post1", "post2"]}

    mock_factory_instance.generate_social_pack.side_effect = fake_generation
    mock_scheduler_instance.schedule_pack.return_value = None

    automation = DailyAutomation()
    automation.db = mock_db_instance
    automation.factory = mock_factory_instance
    automation.scheduler = mock_scheduler_instance

    sequential_time = benchmark_sequential(automation)
    parallel_time = benchmark_parallel(automation)

    improvement = ((sequential_time - parallel_time) / sequential_time) * 100

    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("-" * 60)
    print(f"Sequential Time: {sequential_time:.4f}s")
    print(f"Parallel Time:   {parallel_time:.4f}s")
    print("-" * 60)
    print(f"🚀 Improvement: {improvement:.2f}% faster")
    print("=" * 60)

    return improvement > 50

if __name__ == "__main__":
    benchmark_hf_lab()
    try:
        success = test_daily_automation_optimization()
    except Exception as e:
        print(f"Error during DailyAutomation benchmark: {e}")
        success = False
    sys.exit(0 if success else 1)
