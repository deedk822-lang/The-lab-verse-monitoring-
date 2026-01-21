# Lab-Verse Agent: Complete Migration to Hugging Face

**Status:** ✅ Production-Ready | Zero External API Dependencies | 100% Self-Hosted

## What Changed
- Replaced external LLM calls (Anthropic) with local Hugging Face inference.
- Added model download tooling and GPU-aware Docker/Docker Compose.
- Added HF configuration and a shared model loader.

## Quick Start
```bash
pip install -r requirements-huggingface.txt
chmod +x scripts/download-models.sh && ./scripts/download-models.sh
cp .env.example .env.production
# Fill BITBUCKET_* and HF_* variables
docker-compose up -d
curl http://localhost:8000/health
```

## Notes
- Models are cached locally after first download.
- Use `HF_LOAD_IN_8BIT=true` for lower VRAM GPUs.
