# benchmark.py
import time
from openai import OpenAI

def benchmark_throughput():
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    start = time.time()
    for i in range(10):
        response = client.chat.completions.create(
            model="Qwen/Qwen-72B-Instruct",
            messages=[{"role": "user", "content": f"Count to {i*100}"}],
            max_tokens=100
        )
    elapsed = time.time() - start
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    print(f"Throughput: {10/elapsed:.2f} req/sec")
