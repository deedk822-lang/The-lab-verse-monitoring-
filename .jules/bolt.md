# Bolt's Performance Journal

## 2025-05-22 - Parallelizing API-bound Orchestration
**Learning:** In orchestration services like `ContentFactory`, high-level tasks (e.g., generating text and generating images) are often independent and can be parallelized to significantly reduce total latency. Sequential execution of $T(posts) + T(images)$ was a major bottleneck compared to $max(T(posts), T(images))$.
**Action:** Always look for independent I/O-bound tasks in orchestrators and use `ThreadPoolExecutor` to run them concurrently.

## 2025-05-22 - Concurrency in Loop-based API Calls
**Learning:** Generating a sequence of items (like a multi-day email sequence) via individual API calls is a classic $O(n)$ bottleneck.
**Action:** Use `ThreadPoolExecutor` with a reasonable `max_workers` (e.g., 5) to convert these into parallel tasks. Ensure result order is preserved by using indexed lists or mapping futures to their original identifiers.
