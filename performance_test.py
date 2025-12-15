import time
import sys
import os
import logging
import importlib

# Ensure the script can find the 'vaal-ai-empire' module.
# This assumes the script is run from the root of the repository.
sys.path.insert(0, os.path.abspath(os.getcwd()))


# Disable excessive logging from SentenceTransformer during benchmark
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("sentence_transformers")
logger.setLevel(logging.ERROR)


# --- Define the Original (un-optimized) implementation for comparison ---
# We do this in-memory to avoid having to revert the file.
class OriginalHuggingFaceLab:
    """A recreation of the original, un-optimized class."""
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        # This is the expensive operation that was repeated on every instantiation.
        try:
            self.seo_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            self.seo_model = None

# --- Import the Optimized implementation from the actual refactored code ---
try:
    # The directory 'vaal-ai-empire' has a hyphen, so we must use importlib
    # to import the module dynamically.
    hf_lab_module = importlib.import_module("vaal-ai-empire.src.core.hf_lab")
    OptimizedHuggingFaceLab = hf_lab_module.HuggingFaceLab
except ImportError as e:
    print(f"ERROR: Could not import the optimized HuggingFaceLab: {e}")
    print("Please ensure you are running this script from the repository root and that 'vaal-ai-empire' exists.")
    sys.exit(1)


def benchmark_instantiation(cls, iterations=3):
    """Benchmarks the time it takes to create N instances of a class."""
    print(f"--- Benchmarking {cls.__name__} ({iterations} iterations) ---")
    start_time = time.perf_counter()
    # Create instances in a loop
    for i in range(iterations):
        print(f"  Instance {i+1}/{iterations}...", end='\r')
        _ = cls()
    end_time = time.perf_counter()
    print("\n" + "-" * 30)
    total_time = end_time - start_time
    avg_time = total_time / iterations
    print(f"Total time: {total_time:.4f}s")
    print(f"Average time per instantiation: {avg_time:.4f}s\n")
    return total_time

def test_optimization():
    """Compares the performance of the original vs. optimized class."""
    print("=" * 60)
    print("⚡ BOLT: Performance Benchmark Test ⚡")
    print("=" * 60)
    print("Objective: Verify that caching the SentenceTransformer model")
    print("improves the instantiation speed of the HuggingFaceLab class.")
    print("-" * 60)

    # Benchmark the original, slow implementation
    original_total_time = benchmark_instantiation(OriginalHuggingFaceLab, iterations=3)

    # Benchmark the optimized implementation. The first run includes the one-time
    # cost of loading the model.
    optimized_first_run_time = benchmark_instantiation(OptimizedHuggingFaceLab, iterations=3)

    # Benchmark the optimized implementation again. This run should be MUCH faster
    # as the model is now cached.
    optimized_cached_run_time = benchmark_instantiation(OptimizedHuggingFaceLab, iterations=3)

    print("=" * 60)
    print("📊 Benchmark Results Summary 📊")
    print("=" * 60)
    print(f"Original Implementation (Avg per instance):      {original_total_time/3:.4f}s")
    print(f"Optimized Implementation (1st Run, Avg):       {optimized_first_run_time/3:.4f}s")
    print(f"Optimized Implementation (2nd Run, Cached, Avg): {optimized_cached_run_time/3:.4f}s")
    print("-" * 60)

    # The true comparison is between the original and the cached run.
    # A small tolerance is added to avoid floating point inaccuracies.
    if original_total_time > optimized_cached_run_time + 0.001:
        improvement = ((original_total_time - optimized_cached_run_time) / original_total_time) * 100
        print(f"✅ SUCCESS: Cached run was {improvement:.1f}% faster than the original.")
        return True
    else:
        print("❌ FAILURE: The cached implementation was not significantly faster.")
        print("This could indicate an issue with the @lru_cache implementation.")
        return False

if __name__ == "__main__":
    # Ensure a dummy key is set to avoid errors if the real key isn't in the env
    if "HUGGINGFACE_API_KEY" not in os.environ:
        os.environ["HUGGINGFACE_API_KEY"] = "test-key"

    success = test_optimization()
    sys.exit(0 if success else 1)
