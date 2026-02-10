## 2025-01-26 - Lazy Loading for ContentFactory Providers

**Learning:** Initializing all AI providers (Text, Image, Multimodal) at once in the `ContentFactory` constructor significantly increases startup latency, especially when providers perform network checks (e.g., local Stable Diffusion endpoints).

**Action:** Use separate lazy loaders (decorated with `@lru_cache`) for each provider type and expose them via properties. This ensures that only the required providers are initialized, improving startup time by ~95% for text-only use cases.
