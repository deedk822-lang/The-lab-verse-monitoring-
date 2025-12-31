
import time
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from typing import Dict

# Ensure the vaal-ai-empire directory is in the Python path
sys.path.insert(0, os.path.abspath('./vaal-ai-empire'))

# --- Mock API and Generator Classes ---
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

# --- Original ContentFactory (for baseline) ---
class OriginalContentFactory:
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
        providers = {}
        try:
            from api.cohere import CohereAPI
            providers["cohere"] = CohereAPI()
        except (ImportError, ValueError):
            providers["cohere"] = None
        try:
            from api.groq_api import GroqAPI
            providers["groq"] = GroqAPI()
        except (ImportError, ValueError):
            providers["groq"] = None
        try:
            from api.mistral import MistralAPI
            providers["mistral"] = MistralAPI()
        except (ImportError, ValueError):
            providers["mistral"] = None
        try:
            from api.huggingface_api import HuggingFaceAPI
            providers["huggingface"] = HuggingFaceAPI()
        except (ImportError, ValueError):
            providers["huggingface"] = None
        return providers

    def get_provider_status(self):
        return {k: "available" if v else "unavailable" for k, v in self.providers.items()}

# --- Benchmarking Functions ---
def setup_mocks_for_benchmark():
    """Create a patcher context to mock all external dependencies."""
    module_patcher = patch.dict('sys.modules', {
        'api.cohere': MagicMock(),
        'api.groq_api': MagicMock(),
        'api.mistral': MagicMock(),
        'api.huggingface_api': MagicMock(),
        'api.image_generation': MagicMock(),
    })

    patchers = [
        patch('api.image_generation.BusinessImageGenerator', new=MockBusinessImageGenerator),
        patch('api.huggingface_api.HuggingFaceAPI', new=MockHuggingFaceAPI),
        patch('api.mistral.MistralAPI', new=MockMistralAPI),
        patch('api.groq_api.GroqAPI', new=MockGroqAPI),
        patch('api.cohere.CohereAPI', new=MockCohereAPI),
    ]

    module_patcher.start()
    for p in patchers:
        p.start()

    def stop_all():
        for p in patchers:
            p.stop()
        module_patcher.stop()

    return stop_all

def benchmark_instantiation(cls, iterations=100):
    """Generic function to benchmark class instantiation."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        _ = cls(db=MagicMock())
    end_time = time.perf_counter()
    return end_time - start_time

def test_optimization():
    """
    Main function to run the benchmark and compare original vs. optimized.
    """
    print("=" * 60)
    print("⚡ Bolt: Verifying ContentFactory Optimization ⚡")
    print("=" * 60)

    # --- Run Original Benchmark ---
    stop_mocks = setup_mocks_for_benchmark()
    try:
        original_total_time = benchmark_instantiation(OriginalContentFactory)
        avg_original_ms = (original_total_time / 100) * 1000
        print("--- Original Performance ---")
        print(f"Total time for 100 instantiations: {original_total_time:.4f}s")
        print(f"Average time per instantiation: {avg_original_ms:.2f}ms")
    finally:
        stop_mocks()

    # --- Run Optimized Benchmark ---
    stop_mocks = setup_mocks_for_benchmark()
    try:
        from services.content_generator import ContentFactory as OptimizedContentFactory

        optimized_total_time = benchmark_instantiation(OptimizedContentFactory)
        avg_optimized_ms = (optimized_total_time / 100) * 1000
        print("\n--- Optimized Performance (Lazy Loading) ---")
        print(f"Total time for 100 instantiations: {optimized_total_time:.4f}s")
        print(f"Average time per instantiation: {avg_optimized_ms:.2f}ms")

        print("\n--- Correctness Verification ---")
        print("✓ Correctness verified: Class instantiates without error.")

    finally:
        stop_mocks()

    # --- Results ---
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("-" * 60)

    if original_total_time > 0:
        improvement = ((original_total_time - optimized_total_time) / original_total_time) * 100
        print(f"Original:  {avg_original_ms:.2f}ms per instantiation")
        print(f"Optimized: {avg_optimized_ms:.2f}ms per instantiation")
        print(f"\n🚀 Improvement: {improvement:.1f}% faster")
    else:
        print("Original implementation was too fast to measure, cannot calculate improvement.")
        improvement = 0

    print("=" * 60)
    return improvement > 10

if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
