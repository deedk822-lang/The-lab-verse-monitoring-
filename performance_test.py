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
    sys.exit(0 if success else 1)
