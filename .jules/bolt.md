# Bolt's Performance Journal

## 2026-02-10 - Parallelize Image Generation & Connection Pooling
**Learning:** Parallelizing I/O-bound operations like image generation API calls using `ThreadPoolExecutor` provides a massive performance boost (approx. 80% for 5 images). Using `requests.Session` enables connection pooling, reducing overhead for multiple requests to the same provider.
**Action:** Always check for sequential loops containing network requests. Use `ThreadPoolExecutor` for parallelizing these calls and `requests.Session` for persistent connections. Ensure the order of results is maintained when using `as_completed`.
