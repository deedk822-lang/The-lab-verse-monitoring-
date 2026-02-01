## 2025-05-15 - Parallelizing Image Generation
**Learning:** Sequential image generation is a major bottleneck in the social pack creation workflow. Using `ThreadPoolExecutor` can significantly reduce the total time for batch generation, especially when multiple API providers are available.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` for batch operations that involve external API calls.

## 2025-05-15 - HTTP Connection Pooling
**Learning:** Recreating HTTP connections for every request to the same host adds unnecessary latency. `requests.Session` provides connection pooling which is particularly effective for multiple sequential or parallel requests to the same API endpoint.
**Action:** Always use `requests.Session()` (or `httpx.AsyncClient()` for async code) when making multiple requests to the same provider.
