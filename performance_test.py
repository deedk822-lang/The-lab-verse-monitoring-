import time
import sys
from unittest.mock import patch, MagicMock

# --- Original (Eager-Loading) Implementation ---
# Copied here to create a stable benchmark baseline, as the original file is modified.
class OriginalContentFactory:
    def __init__(self, db=None):
        self.db = db
        self.providers = self._initialize_providers()

    def _initialize_providers(self):
        providers = {"cohere": None, "groq": None, "mistral": None, "huggingface": None}
        try:
            from api.cohere import CohereAPI
            providers["cohere"] = CohereAPI()
        except (ImportError, ValueError):
            pass
        try:
            from api.groq_api import GroqAPI
            providers["groq"] = GroqAPI()
        except (ImportError, ValueError):
            pass
        try:
            from api.mistral import MistralAPI
            providers["mistral"] = MistralAPI()
        except (ImportError, ValueError):
            pass
        try:
            from api.huggingface_api import HuggingFaceAPI
            providers["huggingface"] = HuggingFaceAPI()
        except (ImportError, ValueError):
            pass
        return providers

# --- Optimized (Lazy-Loading) Implementation ---
# We need to add the subdirectory to the path to import the module correctly.
sys.path.insert(0, 'vaal-ai-empire')
from services.content_generator import ContentFactory as OptimizedContentFactory

# --- Mocking Dependencies ---
# Mock the API modules to prevent ImportError and isolate the test
# to the instantiation logic of the ContentFactory itself.
mock_cohere = MagicMock()
mock_groq = MagicMock()
mock_mistral = MagicMock()
mock_huggingface = MagicMock()
mock_image_gen = MagicMock()

# --- Benchmarking Logic ---
def benchmark_instantiation(factory_class, iterations=1000):
    """Measures the time taken to instantiate a class over many iterations."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        _ = factory_class()
    end_time = time.perf_counter()
    return end_time - start_time

def run_performance_test():
    """Compares the performance of the original and optimized factories."""
    print("=" * 60)
    print("⚡ Bolt: Performance Benchmark Test ⚡")
    print("=" * 60)
    print("Target: ContentFactory Instantiation")
    print("Optimization: Lazy-loading of API provider clients.")
    print("-" * 60)

    iterations = 5000

    # Mock all external API dependencies before running the benchmark
    with patch.dict('sys.modules', {
        'api.cohere': mock_cohere,
        'api.groq_api': mock_groq,
        'api.mistral': mock_mistral,
        'api.huggingface_api': mock_huggingface,
        'api.image_generation': mock_image_gen,
    }):
        # Benchmark Original
        print(f"Running benchmark for Original Eager-Loading version ({iterations} iterations)...")
        original_time = benchmark_instantiation(OriginalContentFactory, iterations)
        print(f"  -> Original Total Time: {original_time:.6f}s")
        print(f"  -> Original Avg. Time:  {(original_time / iterations) * 1e6:.2f} µs per instantiation")

        # Benchmark Optimized
        print(f"\nRunning benchmark for Optimized Lazy-Loading version ({iterations} iterations)...")
        optimized_time = benchmark_instantiation(OptimizedContentFactory, iterations)
        print(f"  -> Optimized Total Time: {optimized_time:.6f}s")
        print(f"  -> Optimized Avg. Time:  {(optimized_time / iterations) * 1e6:.2f} µs per instantiation")

    print("-" * 60)

    # Calculate and display results
    if optimized_time > 0 and original_time > optimized_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        times_faster = original_time / optimized_time
        print(f"✅ SUCCESS: Optimized version is {improvement:.2f}% faster.")
        print(f"   (Approximately {times_faster:.1f}x faster)")
    elif original_time < optimized_time:
        print("⚠️  REGRESSION: Optimized version is slower.")
    else:
        print("ℹ️  NO CHANGE: No significant performance change detected.")

    print("=" * 60)

if __name__ == "__main__":
    run_performance_test()
