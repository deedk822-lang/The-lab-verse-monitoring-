# Kimi Computer - Groq Edition

This is the upgraded, serverless version of Kimi Computer, powered by Groq for ultra-fast AI inference and deployed on Vercel Edge for global, zero-latency access.

## Architecture

- **AI Inference**: Groq (Mistral-7B, Mixtral-8x7B, Mistral-Small)
- **Deployment**: Vercel Edge Functions
- **Automation**: Make.com
- **Social Media**: Ayrshare
- **Database**: Notion
- **Monetization**: Brave Ads (BAT)

## Setup and Deployment

1.  **Clone the repository.**
2.  **Create a `.env` file** in the `kimi-computer` directory, using `.env.example` as a template. Fill in your API keys for Groq, Ayrshare, Make.com, and Notion.
3.  **Install dependencies**:
    ```bash
    npm install
    ```
4.  **Deploy to Vercel**:
    ```bash
    vercel --prod
    ```
5.  **Update the Make.com webhook URL** with the URL provided by your Vercel deployment.

## Verification

- Your Vercel deployment should show "Ready".
- The Make.com AI agents should list Groq as the provider.
- You can test the endpoint with `curl`:
  ```bash
  curl -X POST https://your-app.vercel.app/api/groq-mistral \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
  ```
- BAT tips should still be flowing into your Notion database.
- Your daily digest should still be auto-tweeting.
