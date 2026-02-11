# Bolt's Performance Journal

## 2025-05-15 - Lazy Provider Initialization
**Learning:** Initializing multiple AI provider SDKs (Cohere, Groq, etc.) eagerly in a `ContentFactory` constructor can add seconds of latency to application startup, especially if some providers are slow to timeout or perform local discovery (like Stable Diffusion).
**Action:** Use lazy properties and `@lru_cache` for provider initialization so the cost is only paid when a specific provider is first used.

## 2025-05-15 - Parallelizing Independent AI Tasks
**Learning:** Operations that involve both LLM text generation and Image generation are perfect candidates for parallelization because they usually target different endpoints and have significant network/processing latency.
**Action:** Use `ThreadPoolExecutor` to run independent AI generation tasks concurrently, which can reduce total latency by up to 50%.
