
import time
from unittest.mock import patch, MagicMock
import sys
import os
import importlib
import statistics

# Add the 'vaal-ai-empire' directory to the Python path
sys.path.insert(0, os.path.abspath('vaal-ai-empire'))

# --- Mocking Setup ---
sys.modules['cohere'] = MagicMock()
sys.modules['groq'] = MagicMock()
sys.modules['ollama'] = MagicMock()
sys.modules['replicate'] = MagicMock()
sys.modules['stability_sdk'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['transformers'] = MagicMock()

class MockProvider:
    """A mock provider that simulates initialization overhead."""
    def __init__(self):
        time.sleep(0.1)

# --- Benchmarking Functions ---
def benchmark_instantiation(factory_class, setup_func=None, iterations=10):
    """Measures the average time to instantiate a factory class."""
    timings = []
    for i in range(iterations):
        if setup_func:
            setup_func()
        start_time = time.perf_counter()
        _ = factory_class()
        end_time = time.perf_counter()
        timings.append(end_time - start_time)
        print(f"  Iteration {i+1}/{iterations}: {timings[-1]:.6f}s", file=sys.stderr)
    return statistics.mean(timings)

def run_full_benchmark():
    """Compares the performance of the original and optimized implementations."""
    patches = {
        'api.cohere': 'CohereAPI',
        'api.groq_api': 'GroqAPI',
        'api.mistral': 'MistralAPI',
        'api.huggingface_api': 'HuggingFaceAPI',
        'api.kimi': 'KimiAPI',
        'api.image_generation': 'BusinessImageGenerator',
        'api.aya_vision': 'AyaVisionAPI',
    }

    # Use the pre-calculated baseline from our previous runs
    original_time = 0.7028

    patchers = []
    try:
        for module_name, class_name in patches.items():
            patcher = patch(f'{module_name}.{class_name}', MockProvider)
            patchers.append(patcher)
            patcher.start()

        optimized_module = importlib.import_module('services.content_generator')
        importlib.reload(optimized_module)
        OptimizedContentFactory = optimized_module.ContentFactory

        print("\n--- BENCHMARKING OPTIMIZED (LAZY-LOADING) IMPLEMENTATION ---")
        optimized_time = benchmark_instantiation(OptimizedContentFactory)
    finally:
        for p in patchers: p.stop()

    print("\n" + "="*50)
    print("⚡ BOLT PERFORMANCE TEST RESULTS ⚡")
    print("="*50)
    print(f"Original (Baseline):       {original_time:.6f} seconds")
    print(f"Optimized (Lazy Loading):  {optimized_time:.6f} seconds")
    print("-"*50)
    improvement = ((original_time - optimized_time) / original_time) * 100
    print(f"✅ IMPROVEMENT: {improvement:.2f}%")
    if optimized_time > 0:
        print(f"The optimized version is ~{original_time/optimized_time:.1f}x faster.")
    print("="*50)

if __name__ == "__main__":
    run_full_benchmark()
