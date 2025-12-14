# Content Creator AI 🚀

A full-stack JavaScript application for AI-powered content creation with support for multiple AI providers including Google Gemini, LocalAI, Z.AI GLM-4.6, and OpenAI.

## Features ✨

- **Multi-Provider Support**: Switch between Google Gemini, LocalAI, Z.AI GLM-4.6, OpenAI, and more
- **Multi-Modal Content**: Generate text, images, videos, audio, and multimodal content
- **AI-Powered Research**: Real-time research with Google Search integration
- **SEO Optimization**: Automatic SEO metadata generation
- **Social Media**: Auto-generate posts for Twitter, LinkedIn, Facebook, Instagram
- **Real-Time Updates**: WebSocket-based progress tracking
- **Cost Tracking**: Monitor API usage and costs across providers
- **Caching**: Redis-based caching for improved performance
- **Rate Limiting**: Built-in API rate limiting and authentication

## Architecture 🏗️

```
content-creator-ai/
├── config/              # Configuration files
├── controllers/         # Request handlers
├── services/           
│   └── providers/      # AI provider integrations
├── routes/             # API routes
├── middlewares/        # Authentication, rate limiting
├── utils/              # Logger, cache, validators
├── public/             # Static files (CSS, JS)
├── views/              # EJS templates
└── logs/               # Application logs
```

## AI Providers 🤖

### 1. Google for Developers
- **Gemini 1.5 Pro**: Advanced text generation with real-time search
- **Imagen 3.0**: High-quality image generation
- **Veo 3.1**: Video generation and animation
- **Vision API**: Image analysis and understanding

### 2. LocalAI (Self-Hosted)
- **Free & Privacy-Focused**: Run models locally
- **OpenAI-Compatible API**: Drop-in replacement
- **Multiple Models**: Llama, Stable Diffusion, Piper TTS
- **Offline Capable**: No internet required

### 3. Z.AI GLM-4.6
- **Cost-Efficient**: Lower token consumption
- **Long Context**: Up to 200K tokens
- **Thinking Mode**: Advanced reasoning for complex tasks
- **Agentic Capabilities**: Tool use and workflows
- **Streaming Support**: Real-time response generation

### 4. OpenAI
- **GPT-4 Turbo**: Powerful text generation
- **DALL-E 3**: High-quality image generation
- **Whisper**: Audio transcription
- **TTS**: Text-to-speech synthesis

## Quick Start 🚀

### Prerequisites

- Node.js >= 18.0.0
- npm or yarn
- (Optional) Redis for caching
- (Optional) LocalAI server for local inference

### Installation

1. **Clone or navigate to the directory**:
```bash
cd content-creator-ai
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Required: Choose at least one provider
GOOGLE_API_KEY=your-google-ai-studio-key
OPENAI_API_KEY=your-openai-key
ZAI_API_KEY=your-z-ai-key

# Optional: LocalAI
LOCALAI_URL=http://localhost:8080
LOCALAI_ENABLED=true

# Server Configuration
PORT=3000
API_KEY=your-secure-api-key-here

# Default Provider
DEFAULT_PROVIDER=google
```

4. **Start the server**:
```bash
npm start
```

For development with auto-reload:
```bash
npm run dev
```

5. **Access the application**:
- Web UI: http://localhost:3000
- API: http://localhost:3000/api/content
- Health: http://localhost:3000/api/health

## LocalAI Setup 🔧

### Quick Start with LocalAI

1. **Install LocalAI**:
```bash
# Using Docker
docker run -p 8080:8080 --name local-ai -ti localai/localai:latest-aio-cpu

# Or download the binary
curl https://localai.io/install.sh | sh
```

2. **Run LocalAI with a model**:
```bash
# Using the CLI
local-ai run llama-3.2-1b-instruct

# Or with Docker
docker run -p 8080:8080 localai/localai:latest llama-3.2-1b-instruct
```

3. **Configure in .env**:
```env
LOCALAI_URL=http://localhost:8080
LOCALAI_ENABLED=true
```

4. **Test the connection**:
```bash
curl http://localhost:8080/v1/models
```

For more details, see: https://localai.io/docs/getting-started/

## API Usage 📡

### Create Content

**Endpoint**: `POST /api/content`

**Authentication**: Include API key in header:
```
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "topic": "The future of artificial intelligence",
  "media_type": "text",
  "provider": "google",
  "audience": "tech enthusiasts",
  "tone": "professional",
  "language": "en",
  "length": "medium",
  "format": "markdown",
  "enable_research": true,
  "include_seo": true,
  "include_social": true,
  "thinking_mode": false,
  "temperature": 0.7
}
```

**Response**:
```json
{
  "success": true,
  "requestId": "uuid-here",
  "content": {
    "type": "text",
    "content": "# Article content here...",
    "format": "markdown",
    "research": "Research summary...",
    "sources": ["https://example.com"],
    "usage": { "inputTokens": 100, "outputTokens": 500 },
    "totalCost": 0.0125,
    "provider": "google"
  },
  "seo": {
    "title": "The Future of AI",
    "metaDescription": "...",
    "keywords": ["ai", "future", "technology"],
    "readabilityScore": { "score": 75, "level": "Fairly Easy" }
  },
  "social": {
    "twitter": { "text": "...", "length": 280 },
    "linkedin": { "text": "..." },
    "facebook": { "text": "..." }
  },
  "costs": {
    "totalCost": 0.0125
  }
}
```

### Media Types

- `text`: Articles, blog posts (supports markdown, HTML, plain text)
- `image`: Generate images with prompts
- `video`: Create video content (Veo/LocalAI)
- `audio`: Text-to-speech generation
- `multimodal`: Combined text and image

### Test Endpoint

Test without real API calls:
```bash
curl http://localhost:3000/api/test
```

### Health Check

```bash
curl http://localhost:3000/api/health
```

### Get Statistics

```bash
curl -H "X-API-Key: your-api-key" http://localhost:3000/api/stats
```

## Provider-Specific Features

### Google Gemini
- Real-time Google Search integration
- Google Maps data
- Advanced vision capabilities
- Grounded responses with citations

### LocalAI
- 100% private and offline
- Free to use (self-hosted)
- Multiple model support
- AIO images for quick setup

### Z.AI GLM-4.6
- **Thinking Mode**: Enable for complex reasoning
```json
{
  "thinking_mode": true
}
```
- **Long Context**: Up to 200K tokens
- **Cost Efficient**: Lower pricing than alternatives
- **Streaming**: Real-time response generation
- **Agentic**: Tool use and workflows

### OpenAI
- Industry-standard models
- High-quality image generation (DALL-E 3)
- Advanced TTS with multiple voices
- Vision capabilities (GPT-4V)

## Deployment 🚀

### Replit Deployment

1. Import this project to Replit
2. Set environment variables in Replit Secrets:
   - `GOOGLE_API_KEY`
   - `OPENAI_API_KEY`
   - `ZAI_API_KEY`
   - `API_KEY`
3. Click "Run"

### Docker Deployment

```bash
# Build image
docker build -t content-creator-ai .

# Run container
docker run -p 3000:3000 \
  -e GOOGLE_API_KEY=your-key \
  -e API_KEY=your-api-key \
  content-creator-ai
```

### Production Deployment

1. Set `NODE_ENV=production`
2. Use a process manager (PM2):
```bash
npm install -g pm2
pm2 start server.js --name content-creator
```
3. Enable Redis for caching:
```env
REDIS_ENABLED=true
REDIS_URL=redis://your-redis-url
```
4. Configure reverse proxy (nginx/Apache)
5. Enable HTTPS

## Cost Optimization 💰

### Tips for Reducing Costs

1. **Use LocalAI** for development and privacy-focused workloads
2. **Enable caching** with Redis to avoid duplicate API calls
3. **Choose Z.AI GLM-4.6** for cost-efficient long-form content
4. **Set appropriate token limits** in requests
5. **Monitor usage** with the `/api/stats` endpoint

### Cost Comparison (Approximate)

| Provider | Text (1K tokens) | Image | Notes |
|----------|------------------|-------|-------|
| Google Gemini | $0.00125-0.005 | $0.04 | Real-time search included |
| Z.AI GLM-4.6 | $0.0005-0.0015 | N/A | Most cost-efficient |
| OpenAI GPT-4 | $0.01-0.03 | $0.04-0.12 | Premium quality |
| LocalAI | $0 | $0 | Free (self-hosted) |

## Configuration Options ⚙️

### Environment Variables

See `.env.example` for all available options.

### Rate Limiting

Default: 100 requests per minute. Configure in `.env`:
```env
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
```

### Logging

Configure log level:
```env
LOG_LEVEL=info  # debug, info, warn, error
```

## Troubleshooting 🔧

### Common Issues

1. **"No AI providers enabled"**
   - Solution: Set at least one provider API key in `.env`

2. **LocalAI connection failed**
   - Solution: Ensure LocalAI is running on configured URL
   - Test: `curl http://localhost:8080/readyz`

3. **Rate limit exceeded**
   - Solution: Increase limits in `.env` or wait

4. **WebSocket not connecting**
   - Solution: Check firewall/proxy settings for WebSocket support

## API Reference 📚

### Content Request Schema

```typescript
interface ContentRequest {
  topic: string;                    // Required
  media_type: 'text' | 'image' | 'video' | 'audio' | 'multimodal';
  provider?: 'auto' | 'google' | 'localai' | 'zai' | 'openai';
  audience?: string;
  tone?: 'professional' | 'casual' | 'friendly' | 'formal' | 'humorous' | 'technical';
  language?: string;
  
  // Text options
  length?: 'short' | 'medium' | 'long';
  format?: 'markdown' | 'html' | 'plain';
  
  // Media options
  aspect_ratio?: '1:1' | '16:9' | '9:16' | '4:3' | '3:4';
  style?: string;
  duration?: number;
  voice?: string;
  
  // Advanced
  enable_research?: boolean;
  include_seo?: boolean;
  include_social?: boolean;
  thinking_mode?: boolean;
  temperature?: number;
  max_tokens?: number;
}
```

## Contributing 🤝

Contributions are welcome! Please feel free to submit issues or pull requests.

## License 📄

MIT License - see LICENSE file for details

## Support 💬

- Documentation: This README
- Issues: GitHub Issues
- Email: your-email@example.com

## Acknowledgments 🙏

- Google for Developers (Gemini, Imagen, Veo)
- LocalAI Project
- Z.AI Team (GLM-4.6)
- OpenAI
- All open-source contributors

---

Built with ❤️ for the AI content creation community
