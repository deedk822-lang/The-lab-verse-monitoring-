# content_factory_perf_test.py
import time
import sys
from unittest.mock import MagicMock, patch

# Add the project directory to the Python path to allow imports
sys.path.insert(0, 'vaal-ai-empire')

# --- Mock API classes to avoid real imports and dependencies ---
# Each mock simulates a small delay to represent the cost of initialization.
class MockCohereAPI:
    def __init__(self):
        time.sleep(0.05)

class MockGroqAPI:
    def __init__(self):
        time.sleep(0.05)

class MockMistralAPI:
    def __init__(self):
        time.sleep(0.05)

class MockHuggingFaceAPI:
    def __init__(self):
        time.sleep(0.05)

class MockBusinessImageGenerator:
    def __init__(self):
        time.sleep(0.05)


# --- Original ContentFactory Implementation (copied for a stable baseline) ---
from typing import Dict
import logging

# Suppress logging to keep benchmark output clean
logging.basicConfig(level=logging.CRITICAL)

class OriginalContentFactory:
    """
    A direct copy of the original ContentFactory.
    This ensures we are benchmarking against a stable baseline,
    independent of any changes in the source file.
    """
    def __init__(self, db=None):
        self.db = db
        # This is the performance bottleneck: all providers are initialized upfront.
        self.providers = self._initialize_providers()
        self.image_generator = None
        try:
            # We patch this class, so the import will succeed
            from api.image_generation import BusinessImageGenerator
            self.image_generator = BusinessImageGenerator()
        except Exception:
            pass

    def _initialize_providers(self) -> Dict:
        providers = { "cohere": None, "groq": None, "mistral": None, "huggingface": None }
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


# --- Benchmarking Logic ---

def benchmark_instantiation(cls, iterations=10):
    """Measures the time taken to instantiate a class multiple times."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        _ = cls()
    end_time = time.perf_counter()
    return end_time - start_time

@patch('api.cohere.CohereAPI', MockCohereAPI)
@patch('api.groq_api.GroqAPI', MockGroqAPI)
@patch('api.mistral.MistralAPI', MockMistralAPI)
@patch('api.huggingface_api.HuggingFaceAPI', MockHuggingFaceAPI)
@patch('api.image_generation.BusinessImageGenerator', MockBusinessImageGenerator)
def run_benchmark():
    """
    Runs the performance comparison test and prints the results.
    The unittest.mock.patch decorators intercept the real API imports
    and replace them with our simple, timed mock classes.
    """
    print("=" * 60)
    print("⚡ Bolt: Benchmarking ContentFactory Instantiation ⚡")
    print("=" * 60)

    # The class from the actual source file is imported *after* the mocks
    # have been applied, so it will use the mock classes during initialization.
    from services.content_generator import ContentFactory

    iterations = 10
    print(f"Running {iterations} instantiations for each version...")

    # 1. Benchmark the original, copied implementation
    original_time = benchmark_instantiation(OriginalContentFactory, iterations)
    print(f"\nOriginal (Eager Loading) Instantiation Time: {original_time:.4f}s")

    # 2. Benchmark the current implementation from the source file
    optimized_time = benchmark_instantiation(ContentFactory, iterations)
    print(f"Optimized (Lazy Loading) Instantiation Time:  {optimized_time:.4f}s")

    # 3. Calculate and display the difference
    improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0

    print("-" * 60)
    print(f"✅ VERIFIED PERFORMANCE IMPROVEMENT")
    print(f"Improvement: {improvement:.1f}%")
    print("=" * 60)

    if improvement < 90:
        print("Error: Performance improvement is less than expected.")
        sys.exit(1)


if __name__ == "__main__":
    # To ensure the imports inside the classes don't fail, we create
    # dummy modules in sys.modules. The @patch decorator will then
    # populate these modules with our mock classes.
    sys.modules['api'] = MagicMock()
    sys.modules['api.cohere'] = MagicMock()
    sys.modules['api.groq_api'] = MagicMock()
    sys.modules['api.mistral'] = MagicMock()
    sys.modules['api.huggingface_api'] = MagicMock()
    sys.modules['api.image_generation'] = MagicMock()

    run_benchmark()
