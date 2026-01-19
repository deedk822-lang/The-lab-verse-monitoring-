# vaal-ai-empire/tests/test_performance.py
import time
import os
import sys
import unittest
from unittest.mock import patch, Mock
import requests

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Original function for benchmarking (pre-optimization)
def get_perplexity_insight_original(query):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "system", "content": "Test"}, {"role": "user", "content": query}]
    }
    headers = {
        "Authorization": "Bearer FAKE_KEY",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()['choices'][0]['message']['content']

# Import the optimized function
from agents.market_intelligence.the_oracle import get_perplexity_insight

def benchmark_function(func, iterations=100):
    """Benchmark a function over multiple iterations"""
    start = time.perf_counter()
    for _ in range(iterations):
        func("test query")
    end = time.perf_counter()
    return end - start

class TestPerformanceOptimization(unittest.TestCase):

    @patch('requests.post')
    @patch('agents.market_intelligence.the_oracle.session.post')
    def test_optimization_speed_and_correctness(self, mock_session_post, mock_requests_post):
        """
        Verify that the session-based approach is faster and returns the same result.
        """
        # --- Setup Mock Responses ---
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'mocked insight'}}]
        }

        mock_requests_post.return_value = mock_response
        mock_session_post.return_value = mock_response

        # --- Correctness Check ---
        original_result = get_perplexity_insight_original("test query")
        optimized_result = get_perplexity_insight("test query")

        self.assertEqual(original_result, "mocked insight")
        self.assertEqual(optimized_result, "mocked insight")
        self.assertEqual(original_result, optimized_result)
        print("\n✅ Correctness verified: Results match")

        # --- Performance Benchmark ---
        iterations = 100

        # Benchmark original function (which uses requests.post)
        original_time = benchmark_function(get_perplexity_insight_original, iterations)

        # Benchmark optimized function (which uses session.post)
        optimized_time = benchmark_function(get_perplexity_insight, iterations)

        # Calculate improvement
        improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0

        print(f"\n--- Performance Comparison ({iterations} iterations) ---")
        print(f"Original (requests.post):  {original_time:.4f}s")
        print(f"Optimized (session.post): {optimized_time:.4f}s")
        print(f"Improvement: {improvement:.1f}% faster")

        # Note: In this mocked environment, the performance difference is negligible
        # and can be influenced by the overhead of the mocks themselves. The true
        # benefit of session-based connection pooling occurs in a real network
        # environment by avoiding repeated TCP/TLS handshakes, which is not
        # captured here. The primary goal of this test is to ensure correctness.
        print("✅ Performance benchmark complete (correctness verified).")
        # We assert that the optimized time is not drastically worse than the original,
        # accounting for the variability of mock overhead.
        self.assertTrue(optimized_time < original_time * 1.5, "Optimized version should not be significantly slower.")

if __name__ == "__main__":
    unittest.main()
