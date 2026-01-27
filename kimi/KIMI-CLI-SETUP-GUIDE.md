# Kimi CLI setup guide

This repo includes a ready-to-run Kimi package under `kimi/`:

- `kimi/kimi-cli-config.yml` (main config)
- `kimi/kimi-task-prompt.md` (copy/paste prompt)
- `kimi/run-with-kimi.sh` (helper runner)

## Prerequisites

- Python 3.10+
- A `KIMI_API_KEY` from https://platform.moonshot.ai

## Run

```bash
export KIMI_API_KEY=sk-moonshot-your-key
chmod +x kimi/run-with-kimi.sh
./kimi/run-with-kimi.sh
```

## After deployment

Use the validation scripts:

```bash
BASE_URL=http://<server-ip>:8000 ./scripts/health-check.sh
BASE_URL=http://<server-ip>:8000 ./scripts/usage-stats.sh
BASE_URL=http://<server-ip>:8000 ./scripts/test-llm.sh
```
