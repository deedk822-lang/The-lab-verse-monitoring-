
import timeit
import json
import orjson
import pytest

# A sample JSON payload representing a complex AI model response
COMPLEX_JSON_PAYLOAD = b"""
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo-0613",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "{\\"company_name\\": \\"InnovateTech\\", \\"summary\\": \\"A forward-thinking tech company specializing in AI-driven solutions for various industries.\\", \\"intent_score\\": 8, \\"suggested_action\\": \\"Schedule a demo to showcase our AI analytics platform.\\"}"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 82,
    "completion_tokens": 51,
    "total_tokens": 133
  }
}
"""

def benchmark_json():
    """Benchmarks the standard json library."""
    json.loads(COMPLEX_JSON_PAYLOAD)

def benchmark_orjson():
    """Benchmarks the orjson library."""
    orjson.loads(COMPLEX_JSON_PAYLOAD)

def test_orjson_performance_improvement():
    """
    Tests that orjson provides a significant performance improvement over the standard json library.
    """
    iterations = 10000

    json_time = timeit.timeit(benchmark_json, number=iterations)
    orjson_time = timeit.timeit(benchmark_orjson, number=iterations)

    # Assert that orjson is at least 50% faster than the standard json library.
    # This is a conservative estimate, as the improvement is typically much higher.
    assert orjson_time < (json_time * 0.5), f"orjson is not significantly faster than json. json_time={json_time}, orjson_time={orjson_time}"
