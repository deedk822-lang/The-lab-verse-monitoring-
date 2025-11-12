# 🤖 AI Provider Monitoring & Fallback Service

This repository contains a Vercel serverless function that acts as a multi-provider fallback system for various AI models. It is instrumented with OpenTelemetry to provide detailed observability into performance, errors, and costs, sending all data to Grafana Cloud.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Observability with OpenTelemetry](#observability-with-opentelemetry)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **Multi-Provider Fallback**: Automatically retries requests across multiple AI providers (e.g., OpenAI, Groq) to ensure high availability.
- **Comprehensive Observability**: Uses OpenTelemetry to send traces, metrics, and logs to Grafana Cloud.
- **Detailed Metrics**: Tracks request rates, error rates, latency percentiles, and token usage per provider and model.
- **Distributed Tracing**: Provides end-to-end visibility into the lifecycle of each request.
- **Deployable on Vercel**: Optimized for easy deployment as a serverless function.

---

## 🏗️ Architecture

1.  **Client Request**: A client sends a request to the `/api/research` or `/api/generate` endpoint.
2.  **Vercel Serverless Function**: The Node.js server, running on Vercel, receives the request.
3.  **OpenTelemetry SDK**: The SDK, initialized first, automatically instruments incoming Express requests and outgoing HTTP calls.
4.  **Instrumented Provider Logic**: The `multiProviderGenerateInstrumented` function attempts to call the primary AI provider (e.g., OpenAI).
5.  **Fallback Logic**: If the primary provider fails, it automatically tries the next provider in the chain (e.g., Groq).
6.  **Telemetry Export**: Throughout this process, the OpenTelemetry SDK captures spans (for traces) and metrics, exporting them asynchronously to the Grafana Cloud OTLP endpoint.
7.  **Response**: The successful response from an AI provider is returned to the client.

---

## 📈 Observability with OpenTelemetry

This service uses a robust OpenTelemetry setup to send telemetry data directly to Grafana Cloud's OTLP endpoint.

### Required Environment Variables

To enable observability, you must configure the following environment variables in your Vercel project:

| Variable Name                  | Description                                                                                             | Example Value                                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `OTEL_EXPORTER_OTLP_ENDPOINT`  | The OTLP endpoint URL provided by Grafana Cloud.                                                        | `https://otlp-gateway-prod-us-central-0.grafana.net/otlp`                  |
| `OTEL_EXPORTER_OTLP_PROTOCOL`  | The protocol to use for exporting data.                                                                 | `http/protobuf`                                                            |
| `OTEL_EXPORTER_OTLP_HEADERS`   | The `Authorization` header, containing your Base64-encoded Grafana Cloud credentials.                     | `Authorization=Basic MTIzNDU2OmdsY19leUprSW...`                               |
| `OTEL_SERVICE_NAME`            | The name of your service, which will appear in Grafana.                                                 | `ai-provider-monitoring`                                                   |
| `OTEL_RESOURCE_ATTRIBUTES`     | Additional metadata for your service.                                                                   | `service.name=ai-provider-monitoring,deployment.environment=production`    |

### How to Generate `OTEL_EXPORTER_OTLP_HEADERS`

1.  Find your **Instance ID** and **API Token** in your Grafana Cloud OpenTelemetry connection settings.
2.  Format them as a single string: `INSTANCE_ID:API_TOKEN`.
3.  Base64-encode this string.

**Example Command:**

```bash
echo -n "YOUR_INSTANCE_ID:YOUR_API_TOKEN" | base64
```

### Verifying Data in Grafana Cloud

After deploying and sending a few test requests, wait 30-60 seconds and then check Grafana Cloud:

1.  **Traces (Tempo)**:
    - Go to `Explore` → `Tempo` datasource.
    - Search for traces where `service.name = "ai-provider-monitoring"`.
    - You should see spans for `ai.generate` and `ai.multi_provider_generate`.

2.  **Metrics (Prometheus)**:
    - Go to `Explore` → `Prometheus` datasource.
    - Use the Metrics browser to find metrics like `ai_provider_requests_total`, `ai_provider_errors_total`, and `ai_provider_request_duration_seconds`.

---

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/the-lab-verse-monitoring.git
    cd the-lab-verse-monitoring
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up environment variables:**
    - Copy `.env.example` to `.env` and fill in your AI provider API keys.
    - For deployment, add all required environment variables to your Vercel project settings.

4.  **Deploy to Vercel:**
    ```bash
    vercel --prod
    ```

---

## 🔑 Environment Variables

See `.env.example` for a full list. Key variables include:

- `OPENAI_API_KEY`: Your API key for OpenAI.
- `GROQ_API_KEY`: Your API key for Groq.
- All `OTEL_*` variables listed in the [Observability](#observability-with-opentelemetry) section for deployment.

---

## 📡 API Endpoints

-   **`POST /api/research`**:
    -   Accepts a simple query.
    -   **Body**: `{ "q": "Your question here" }`

-   **`POST /api/generate`**:
    -   Accepts a more complex request with messages and model selection.
    -   **Body**: `{ "messages": [{ "role": "user", "content": "Hello" }], "model": "gpt-4" }`

-   **`GET /health`**:
    -   A simple health check endpoint.
    -   Returns the status and whether telemetry is enabled.

---

## 🔧 Troubleshooting

-   **No data in Grafana**:
    1.  **Verify Environment Variables**: Double-check all `OTEL_*` variables in your Vercel deployment settings. Ensure the Base64 value is correct.
    2.  **Check Vercel Logs**: Run `vercel logs` and look for `"✅ OpenTelemetry initialized"`. If you see errors, they will likely point to an authentication or configuration issue.
    3.  **Wait for Propagation**: It can take 1-2 minutes for the first batch of telemetry data to appear in Grafana.

-   **`401 Unauthorized` errors in logs**:
    -   This almost always means your `OTEL_EXPORTER_OTLP_HEADERS` value is incorrect. Regenerate your Base64-encoded credentials and update the variable in Vercel.
