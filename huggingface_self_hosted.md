# Lab-Verse Agent - Hugging Face Self-Hosted Models (NO EXTERNAL API DEPENDENCIES)

## Purpose
This repository can run its LLM-backed pipeline diagnostics using fully self-hosted Hugging Face models (no Anthropic/z.ai/external APIs).

## Models
- Diagnostic / Validator: `mistralai/Mistral-7B-Instruct-v0.3`
- Planner: `microsoft/phi-2`
- Executor: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`

## One-time model download (~15GB)
```bash
chmod +x scripts/download-models.sh
./scripts/download-models.sh
```

## Environment
Create `.env.production` (or copy from `.env.example`) and set:
- `BITBUCKET_*` credentials
- `HF_*` settings (device, cache dir, model ids)

## Run
```bash
docker-compose up -d
curl http://localhost:8000/health
```
