# Bolt's Journal ⚡

## 2026-02-09 - ThreadPoolExecutor and Empty Inputs
**Learning:** `ThreadPoolExecutor` raises a `ValueError` if `max_workers` is calculated as 0 (e.g., `min(len(prompts), 5)` where `prompts` is empty).
**Action:** Always include an early return or a `max(1, ...)` check when dynamically calculating `max_workers` based on input size.

## 2026-02-09 - Connection Pooling in Image Generation
**Learning:** Reusing HTTP connections via `requests.Session()` significantly reduces latency in multi-provider image generation services, especially when downloading images after API calls (e.g., Replicate).
**Action:** Implement `requests.Session` in all API-heavy classes to improve efficiency.
