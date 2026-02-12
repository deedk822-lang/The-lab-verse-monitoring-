# Bolt ⚡ Performance Journal

## 2026-02-12 - Parallelizing Image Batch Generation
**Learning:** Parallelizing I/O-bound API calls in `generate_batch` using `ThreadPoolExecutor` provides a massive speedup (up to 80% for small batches) without changing the core generation logic.
**Action:** Always look for sequential loops containing network requests (API calls) and consider `ThreadPoolExecutor` or `asyncio.gather`.

## 2026-02-12 - HTTP Connection Pooling
**Learning:** Using `requests.Session` is critical for applications making repeated requests to the same host (e.g., local SD server or external APIs) to avoid the overhead of repeated TCP/TLS handshakes.
**Action:** Replace direct `requests.get/post` with a class-level persistent session.
