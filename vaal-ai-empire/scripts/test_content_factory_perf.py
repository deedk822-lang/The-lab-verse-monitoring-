
"""
⚡ Bolt: Performance Benchmark for ContentFactory Instantiation

This script measures and verifies the performance improvement from refactoring
the ContentFactory to use lazy loading for its API providers.

It compares the original "eager-loading" pattern against the new
"lazy-loading" pattern.
"""
import time
import timeit
import unittest.mock
import importlib
import logging
from typing import Dict

# Disable logging for cleaner benchmark output
logging.basicConfig(level=logging.CRITICAL)

# --- Mocking Setup ---

def slow_initializer(*args, **kwargs):
    """Simulates a slow object initialization (e.g., reading files, network setup)."""
    time.sleep(0.01)  # 10ms delay per provider
    return unittest.mock.MagicMock()

mock_cohere_class = unittest.mock.MagicMock(side_effect=slow_initializer)
mock_groq_class = unittest.mock.MagicMock(side_effect=slow_initializer)
mock_mistral_class = unittest.mock.MagicMock(side_effect=slow_initializer)
mock_huggingface_class = unittest.mock.MagicMock(side_effect=slow_initializer)
mock_image_gen_class = unittest.mock.MagicMock(side_effect=slow_initializer)

modules = {
    'api.cohere': unittest.mock.MagicMock(CohereAPI=mock_cohere_class),
    'api.groq_api': unittest.mock.MagicMock(GroqAPI=mock_groq_class),
    'api.mistral': unittest.mock.MagicMock(MistralAPI=mock_mistral_class),
    'api.huggingface_api': unittest.mock.MagicMock(HuggingFaceAPI=mock_huggingface_class),
    'api.image_generation': unittest.mock.MagicMock(BusinessImageGenerator=mock_image_gen_class),
}

# --- Test Classes ---

class OriginalContentFactory:
    """A local copy of the original, inefficient ContentFactory for benchmarking."""
    def __init__(self, db=None):
        self.db = db
        self.providers = self._initialize_providers()
        self.image_generator = None
        try:
            from api.image_generation import BusinessImageGenerator
            self.image_generator = BusinessImageGenerator()
        except Exception:
            pass

    def _initialize_providers(self) -> Dict:
        providers = {"cohere": None, "groq": None, "mistral": None, "huggingface": None}
        try:
            from api.cohere import CohereAPI
            providers["cohere"] = CohereAPI()
        except (ImportError, ValueError): pass
        try:
            from api.groq_api import GroqAPI
            providers["groq"] = GroqAPI()
        except (ImportError, ValueError): pass
        try:
            from api.mistral import MistralAPI
            providers["mistral"] = MistralAPI()
        except (ImportError, ValueError): pass
        try:
            from api.huggingface_api import HuggingFaceAPI
            providers["huggingface"] = HuggingFaceAPI()
        except (ImportError, ValueError): pass
        return providers

def benchmark_class(cls, name: str, iterations: int = 10) -> float:
    """Benchmarks the instantiation of a given class."""
    stmt_code = f"{cls.__name__}()"

    execution_globals = {
        cls.__name__: cls,
    }

    total_time = timeit.timeit(stmt=stmt_code, number=iterations, globals=execution_globals)
    avg_time = total_time / iterations

    print(f"{name:<20} | Avg. Instantiation Time: {avg_time:.6f} seconds")
    return avg_time

# --- Main Execution ---

if __name__ == "__main__":
    print("=" * 70)
    print("⚡ Bolt: ContentFactory Instantiation Performance Comparison")
    print("-" * 70)
    print("Simulating 10ms initialization delay for each of 5 external clients...")
    print("-" * 70)

    with unittest.mock.patch.dict('sys.modules', modules):
        # Import the optimized class from the actual source file
        content_generator_module = importlib.import_module("vaal-ai-empire.services.content_generator")
        OptimizedContentFactory = content_generator_module.ContentFactory

        # Run benchmarks
        original_time = benchmark_class(OriginalContentFactory, "Original (Eager)")
        optimized_time = benchmark_class(OptimizedContentFactory, "Optimized (Lazy)")

        # Calculate and report improvement
        if optimized_time > 0 and original_time > optimized_time:
            improvement = ((original_time - optimized_time) / original_time) * 100
            print("-" * 70)
            print(f"✅ PASSED: Lazy loading is {improvement:.1f}% faster.")
            print("=" * 70)
        else:
            print("-" * 70)
            print("❌ FAILED: Optimization did not result in a measurable improvement.")
            print("=" * 70)
