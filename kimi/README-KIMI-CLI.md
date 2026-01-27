# Kimi quick reference

## One-liner

```bash
export KIMI_API_KEY=sk-moonshot-your-key
./kimi/run-with-kimi.sh
```

## Notes

- The docker stack uses `KIMIAPIKEY` (see `docker-compose.yml`), while many tools use `KIMI_API_KEY`; the helper script exports both.
- Default API base URL is `http://localhost:8000` for the scripts; override with `BASE_URL`.
