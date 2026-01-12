# benchmark.py
import time
from openai import OpenAI

def benchmark_throughput():
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

    start = time.time()
    for i in range(10):
        response = client.chat.completions.create(
            model="Qwen/Qwen-72B-Instruct",
            messages=[{"role": "user", "content": f"Count to {i*100}"}],
            max_tokens=100
        )
    elapsed = time.time() - start

    print(f"Throughput: {10/elapsed:.2f} req/sec")
