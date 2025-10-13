# Changes Summary

- Added AI Connectivity Layer: dual-engine (Qwen + Kimi) test harness.
- Optional StatsD emission in `lapverse-core/src/cost/FinOpsTagger.ts` to avoid runtime errors when StatsD is absent.
- Added dependencies: axios, zod, dotenv.
- Added `lapverse-core/test-ai-connector.ts` script to validate API keys and simple round-trip.
- Documentation: `QUICKSTART.md`, `SETUP_VERIFICATION_REPORT.md` for setup and validation.
