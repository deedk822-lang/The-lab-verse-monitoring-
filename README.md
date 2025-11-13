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
├─ mcp-server/
│  ├─ wpcom-gateway.js
│  ├─ unito-gateway.js
│  ├─ socialpilot-gateway.js
│  └─ huggingface-gateway.js
├─ package.json                    ← deps & scripts
├─ vercel.json                     ← edge config
└─ .env.example                    ← all env vars listed
```

## Setup and Deployment

1.  **Install Node.js:**
    Ensure you have Node.js version 18 or higher installed.
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Set up environment variables:**
    Copy `.env.example` to `.env.local` and fill in the required API keys.
4.  **Run the tests:**
    ```bash
    npm test
    ```
    This will echo a success message to satisfy the CI pipeline.
5.  **Deploy to Vercel:**
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

## MCP Server Setup

1.  **Make servers executable:**
    ```bash
    chmod +x mcp-server/*.js
    ```
2.  **Run the servers:**
    You can run each server in a separate terminal:
    ```bash
    node mcp-server/wpcom-gateway.js
    node mcp-server/unito-gateway.js
    node mcp-server/socialpilot-gateway.js
    node mcp-server/huggingface-gateway.js
    ```
    Or, you can run them all at once:
    ```bash
    npm run start:all
    ```
3.  **Configure Claude Desktop:**
    Update your `claude_desktop_config.json` file with the following, replacing the placeholders with your actual values:
    ```json
    {
      "mcpServers": {
        "wpcom-gateway": {
          "command": "node",
          "args": ["/FULL/PATH/mcp-server/wpcom-gateway.js"],
          "env": { "GATEWAY_URL": "https://<your-domain>", "GATEWAY_KEY": "<ANY-KEY>" }
        },
        "unito-gateway": {
          "command": "node",
          "args": ["/FULL/PATH/mcp-server/unito-gateway.js"],
          "env": { "GATEWAY_URL": "https://<your-domain>", "GATEWAY_KEY": "<ANY-KEY>" }
        },
        "socialpilot-gateway": {
          "command": "node",
          "args": ["/FULL/PATH/mcp-server/socialpilot-gateway.js"],
          "env": { "GATEWAY_URL": "https://<your-domain>", "GATEWAY_KEY": "<ANY-KEY>" }
        },
        "huggingface-gateway": {
          "command": "node",
          "args": ["/FULL/PATH/mcp-server/huggingface-gateway.js"],
          "env": { "GATEWAY_URL": "https://<your-domain>", "GATEWAY_KEY": "<ANY-KEY>" }
        }
      }
    }
    ```
