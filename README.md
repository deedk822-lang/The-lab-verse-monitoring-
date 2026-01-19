# The Lab Verse Monitoring Stack
A comprehensive, production-ready monitoring infrastructure with **AI-powered project management** through Kimi Instruct - your hybrid AI project manager.

## What is Kimi Instruct?
**Kimi Instruct** is a hybrid AI project manager that combines artificial intelligence with human oversight to manage your monitoring infrastructure project.

### Key Features
- AI-powered task management
- Human-AI collaboration via approval workflows
- Real-time project tracking
- Budget intelligence and cost tracking
- Smart escalation based on severity and impact
- Predictive analytics
- Self-healing operations for common issues
- Multi-interface access (web dashboard, CLI, API)

## Setup Instructions
1. Clone the repository:
```bash
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys (do not commit secrets)
```

4. Start the application:
```bash
npm start
```

For detailed setup instructions, refer to the documentation in the `/docs` directory.

## Architecture Overview
Kimi Instruct sits above a monitoring stack (Prometheus/Grafana/Alertmanager) and integrates with supported AI providers through MCP and related adapters.

## API Endpoints
- `/api/test/health` - Health check for all services (http://localhost:3000/api/test/health)
- `/api/ayrshare/ayr` - Multi-channel content distribution
- `/api/content/generate` - Content generation
- `/api/elevenlabs/tts` - Voice synthesis
- `/api/perplexity/search` - Web search with Perplexity AI

## Supported AI Models
- OpenAI: GPT-4, DALL-E, Whisper, TTS
- Google Gemini: Reasoning and multimodal
- LocalAI: Privacy-focused local inference
- Perplexity AI: Web search and research
- Alibaba Cloud Qwen: Reasoning and coding
- Hugging Face: Open-source model access

## Deployment
Deploy with Docker:
```bash
docker-compose up -d
```

Or deploy to Vercel:
```bash
vercel --prod
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.
