# Bolt's Performance Journal

## 2025-01-26 - Parallelizing social pack generation
**Learning:** In the `vaal-ai-empire` codebase, `ContentFactory.generate_social_pack` was performing text generation and image generation sequentially. Since these are independent I/O-bound tasks involving external API calls, parallelizing them using `ThreadPoolExecutor` provides a ~50% reduction in total latency.
**Action:** Always look for independent API calls in orchestration methods and run them concurrently using a thread pool.

## 2025-01-26 - Lazy loading of heavy AI models
**Learning:** `ContentFactory` was initializing all providers, including a heavy Aya Vision multimodal model (~32B), during `__init__`. This resulted in a >6s startup delay even for scripts that only needed basic text generation.
**Action:** Use lazy initialization or `@lru_cache` on separate loader functions to ensure heavy components are only loaded when actually used.
