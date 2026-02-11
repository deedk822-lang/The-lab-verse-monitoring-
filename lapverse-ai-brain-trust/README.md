<p align="center"><img src="public/logo-dark.svg" height="120"/></p>
<h1 align="center">LapVerse AI Brain Trust</h1>
<p align="center">
  Multi-provider AI notebook with Tongyi DeepResearch & ALPHA Coliseum
</p>
<p align="center">
  <a href="https://codespaces.new/YOU/my-ai-notebook"><img src="https://github.com/codespaces/badge.svg" alt="Open in Codespaces"/></a>
</p>

## 🚀 90-second start
1. Click **“Open in GitHub Codespaces”** above.
2. In the terminal:
   ```bash
   cp .env.example .env.local
   # add your keys (only GEMINI required to run)
   npm install
   npm run dev
   ```
3. Ports tab → open 3000 → done!

## ✨ What's inside
| Feature | Description |
|---------|-------------|
| **Tongyi DeepResearch** | Long-form, multi-source, visual research |
| **ALPHA Coliseum** | AI arena – agents battle for best anomaly fix |
| **Quad-brain core** | Qwen • Kimi • GLM-4.6 • Perplexity |
| **Social publish** | 1-click → 10 platforms via AyShare |
| **Cost guardrails** | Circuit-breakers + quota caps |
| **Observability** | Prometheus metrics + structured logs |

## 🔭 API quick hits
| Endpoint | Purpose |
|----------|---------|
| `POST /api/v2/coliseum?action=create-challenge` | Throw an anomaly into the arena |
| `GET  /api/v2/coliseum?action=leaderboard` | See which AI is winning |
| `POST /api/v2/ai/connect` | Multi-provider prompt (quad-brain) |

## 🔐 Secrets
- Never commit `.env.local` (already ignored).
- Add keys via Codespaces secrets UI – they stay encrypted.

## 📄 Licence
Apache-2.0 – identical to the embedded copyright cell.