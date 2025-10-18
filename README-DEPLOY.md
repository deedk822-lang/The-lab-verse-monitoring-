# Lab-Verse Enhanced – Deploy in 90s

```bash
cp .env.example .env  # fill secrets
docker-compose up -d --build
curl http://localhost:3000/health
```

## API Endpoints:

- `POST /api/video/generate`      (JWT, Joi validated)
- `POST /api/text-to-speech`      (JWT, returns MP3)
- `POST /api/alerts/slack`        (public, queues alert)

## Metrics:

- `GET /health`   (Health check)
- `GET /metrics`  (Prometheus format)

## Quick Test:

```bash
# Generate JWT token for testing
node -e "console.log(require('jsonwebtoken').sign({user:'test'}, process.env.JWT_SECRET))"

# Test video generation
curl -X POST http://localhost:3000/api/video/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A cat playing with a ball","duration":10}'

# Test TTS
curl -X POST http://localhost:3000/api/text-to-speech \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}' \
  --output speech.mp3
```