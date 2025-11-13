# Lab-Verse Universal AI Gateway

This is a complete, copy-paste-ready bundle for a universal AI gateway that can be deployed to Vercel in under 2 minutes.

## Directory Layout

```
repo-root/
├─ pages/
│  └─ api/
│     └─ gateway/
│        └─ v1/
│           └─ chat/
│              └─ completions.js   ← universal chat endpoint
├─ src/
│  ├─ lib/
│  │  ├─ providers.js              ← full provider registry
│  │  └─ telemetry.js              ← thin OTel + cost wrapper
│  └─ monitoring/
│     └─ costTracking.js           ← stub cost tracker
├─ package.json                    ← deps & scripts
├─ vercel.json                     ← edge config
└─ .env.example                    ← all env vars listed
```

## Setup and Deployment

1.  **Install dependencies:**
    ```bash
    npm install
    ```
2.  **Set up environment variables:**
    Copy `.env.example` to `.env.local` and fill in the required API keys.
3.  **Deploy to Vercel:**
    ```bash
    vercel --prod
    ```

## Health Check

You can verify that the gateway is live by running the following command:

```bash
curl -X POST https://<your-domain>/api/gateway/v1/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -d '{"model":"glm-4.6","messages":[{"role":"user","content":"ping"}]}'
```

You should see a response with the following headers:

*   `x-gateway-provider: zai`
*   `x-gateway-model: glm-4.6`
*   `x-trace-id: <otel-trace>`
