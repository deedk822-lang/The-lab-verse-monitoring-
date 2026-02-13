# Bolt's Performance Journal

## 2026-02-13 - Image Generation Parallelization & Session Reuse
**Learning:** Sequential image generation in `ImageGenerator` was a major bottleneck (~2.5s for 5 images with 0.5s latency). Implementing `requests.Session` for connection reuse and `ThreadPoolExecutor` for parallelizing `generate_batch` reduced execution time by ~80% (to ~0.5s).
**Action:** Always check for sequential loops over network-bound tasks and use `requests.Session` when multiple requests are made to the same or different hosts to benefit from connection pooling.
