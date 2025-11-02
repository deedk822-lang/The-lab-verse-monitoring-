# AI Content Creation Suite with Multi-Channel Distribution

A comprehensive fullstack JavaScript application that replicates n8n content creation workflows with support for multiple AI providers and automated multi-channel content distribution.

## 🚀 Features

### Multi-Provider AI Support

- **OpenAI**: GPT-4, DALL-E, Whisper, TTS
- **Google Gemini**: Advanced reasoning, Imagen, Veo, Google Search/Maps integration
- **LocalAI**: Privacy-focused local inference with various models
- **Z.AI GLM-4.6**: Efficient reasoning, tool use, long context (200K tokens)
- **Perplexity AI**: Web search and real-time research capabilities
- **Manus AI**: Creative writing and content optimization
- **Claude AI**: Advanced reasoning and analysis (via MCP)
- **Mistral AI**: Multilingual content generation (via MCP)
- **ElevenLabs**: AI voice synthesis and audio generation

### Multi-Channel Distribution

- **Social Media**: Automated posting via Ayrshare to Twitter, Facebook, LinkedIn, Instagram, YouTube, TikTok, Telegram, Reddit
- **Email Marketing**: MailChimp campaign creation and sending
- **Cross-Platform Communication**: A2A integration with Slack, Teams, Discord, Zapier, IFTTT, n8n, Make
- **Voice Content**: Audio generation and podcast creation with ElevenLabs
- **Webhook Integration**: Zapier-compatible for workflow automation

### Content Generation Capabilities

- **Text**: Articles, blog posts, social media content
- **Images**: High-quality generation with aspect ratio control
- **Videos**: Prompt-based video generation and animation
- **Audio**: Text-to-speech, voice cloning, and audiobook creation
- **Multimodal**: Combined content types with integrated workflows

### Advanced Features

- Real-time progress tracking with WebSockets
- SEO optimization and metadata generation
- Multi-platform content optimization
- Cost tracking and usage analytics
- Caching with Redis for improved performance
- Rate limiting and API key authentication
- Docker support for easy deployment
- MCP (Model Context Protocol) integration
- A2A (Application-to-Application) communication

## 🛠️ Quick Start

### Prerequisites

- Node.js 18+
- Redis (optional, for caching)
- Docker & Docker Compose (for containerized deployment)

### Installation

1. **Clone and setup:**

```bash
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-
npm install
```

2. **Configure API keys in `.env`:**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
# At minimum, configure:
API_KEY=your_secure_api_key_here
OPENAI_API_KEY=your_openai_key  # OR
GOOGLE_API_KEY=your_google_key  # OR any other AI provider

# For multi-channel distribution, also configure:
AYRSHARE_API_KEY=your_ayrshare_key_here           # For social media
MAILCHIMP_API_KEY=your_mailchimp_key_here        # For email
ELEVENLABS_API_KEY=your_elevenlabs_key_here      # For voice
```

3. **Start the application:**

```bash
npm start
```

4. **Open your browser:**

```
http://localhost:3000
```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `PORT` | Server port | 3000 |
| `NODE_ENV` | Environment | development |
| `API_KEY` | API authentication key | - |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |

### AI Provider Configuration

#### Required (at least one)
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_API_KEY` - Google AI API key  
- `ZAI_API_KEY` - Z.AI API key
- `LOCALAI_URL` - LocalAI server URL

#### Optional Enhancement Services
- `PERPLEXITY_API_KEY` - For web search and research
- `MANUS_API_KEY` - For creative writing optimization
- `CLAUDE_API_KEY` - For advanced reasoning (MCP)
- `MISTRAL_API_KEY` - For multilingual content (MCP)
- `ELEVENLABS_API_KEY` - For voice synthesis

### Distribution Services

#### Social Media (Ayrshare)
- `AYRSHARE_API_KEY` - Required for social media posting

#### Email Marketing (MailChimp)
- `MAILCHIMP_API_KEY` - Required for email campaigns
- `MAILCHIMP_SERVER_PREFIX` - Your MailChimp server (e.g., us1)
- `MAILCHIMP_LIST_ID` - Your subscriber list ID

#### Cross-Platform Communication (A2A)
- `A2A_SLACK_WEBHOOK` - Slack webhook URL
- `A2A_TEAMS_WEBHOOK` - Microsoft Teams webhook URL
- `A2A_DISCORD_WEBHOOK` - Discord webhook URL

## 📚 API Reference

### Multi-Channel Distribution

```bash
# Zapier webhook endpoint (primary integration point)
POST /api/ayrshare/ayr
Content-Type: application/json
x-api-key: your-api-key

{
  "topic": "AI Technology Trends",
  "platforms": "twitter,linkedin,facebook,instagram",
  "audience": "tech professionals", 
  "tone": "professional",
  "provider": "perplexity",
  "includeEmail": true,
  "emailSubject": "Latest AI Trends",
  "generateAudio": true,
  "voiceType": "professional"
}
```

### Individual Service Endpoints

```bash
# Social media only
POST /api/ayrshare/post

# Email campaign only  
POST /api/ayrshare/email

# Voice generation only
POST /api/elevenlabs/tts

# Content generation only
POST /api/content/generate

# Test all services
GET /api/test/health
```

### Test Endpoints

```bash
# Test individual services
GET /api/test/ayrshare          # Social media
GET /api/ayrshare/test/mailchimp # Email
GET /api/test/workflow          # Full multi-channel test
GET /api/test/providers         # AI providers
```

## 🏗️ Architecture

```
src/
├── config/          # Provider configurations
├── middleware/      # Authentication, caching, error handling
├── routes/          # API endpoints
│   ├── content.js   # Content generation
│   ├── ayrshare.js  # Multi-channel distribution
│   └── test.js      # Testing endpoints
├── services/        # AI providers and integrations
│   ├── ayrshareService.js     # Social media posting
│   ├── mailchimpService.js    # Email campaigns
│   ├── perplexityService.js   # Web search & research
│   ├── manusService.js        # Creative optimization
│   ├── mcpService.js          # Claude & Mistral integration
│   ├── a2aService.js          # Cross-platform communication
│   └── elevenLabsService.js   # Voice synthesis
├── utils/           # Logging, Redis, utilities
└── server.js        # Main application entry point
```

## 🔌 Integration Examples

### Zapier Integration

1. Create a Zapier webhook trigger
2. Configure action to POST to `/api/ayrshare/ayr`
3. Map webhook data to content parameters
4. Enable automatic multi-channel distribution

### Advanced Workflow Example

```javascript
// Research + Generate + Optimize + Distribute workflow
const workflow = {
  topic: "Sustainable AI Development",
  
  // Research phase (Perplexity)
  research: {
    provider: "perplexity",
    useWebSearch: true,
    focusArea: "recent"
  },
  
  // Generation phase (Multiple providers)
  generation: {
    providers: ["google", "claude", "manus"],
    tone: "authoritative",
    audience: "business leaders"
  },
  
  // Distribution phase
  distribution: {
    social: {
      platforms: ["linkedin", "twitter", "facebook"],
      optimizePerPlatform: true
    },
    email: {
      subject: "Sustainable AI: Industry Report",
      segment: "business_leaders"
    },
    audio: {
      voiceType: "professional",
      generatePodcast: true
    },
    notifications: {
      slack: true,
      teams: true
    }
  }
};
```

## 🧪 Testing

```bash
# Test all providers and services
npm test

# Test specific functionality
curl http://localhost:3000/api/test/health

# Test multi-channel workflow
curl -X POST http://localhost:3000/api/ayrshare/ayr \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"topic":"AI Test","platforms":"twitter,linkedin"}'
```

## 📊 Monitoring

The application includes comprehensive logging and monitoring:

- **Winston** for structured logging
- **Redis** for caching and session management  
- **Health checks** for all providers and services
- **Cost tracking** for API usage
- **Real-time WebSocket** progress updates
- **Performance metrics** and analytics

## 🚀 Deployment

### Production Deployment

1. **Environment Setup:**

```bash
export NODE_ENV=production
export API_KEY=your-secure-production-key
export REDIS_URL=redis://your-redis-server:6379
```

2. **Docker Production:**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Fly.io Deployment:** (Recommended)

```bash
# Install Fly CLI
fly auth login
fly create your-app-name
fly deploy
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: Check the `/docs` directory
- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub Discussions for questions
- **Setup Guide**: See `ZAPIER_AYRSHARE_SETUP.md` for detailed configuration

## 🔄 Recent Updates

### Latest Features

- ✅ **Multi-Channel Distribution**: Ayrshare + MailChimp + A2A integration
- ✅ **Advanced AI Providers**: Perplexity, Manus, Claude, Mistral via MCP
- ✅ **Voice Synthesis**: ElevenLabs integration for audio content
- ✅ **Real-time Monitoring**: WebSocket progress updates
- ✅ **Cross-Platform Communication**: A2A service for team notifications
- ✅ **Enhanced Research**: Web search with Perplexity AI
- ✅ **Creative Optimization**: Content enhancement with Manus AI

### Roadmap

- 🔄 Advanced analytics dashboard
- 🔄 Custom model fine-tuning
- 🔄 Batch processing capabilities
- 🔄 Advanced workflow automation
- 🔄 Multi-language UI support
- 🔄 Video content generation
- 🔄 Advanced A/B testing for content

## About

A comprehensive Node.js server that runs multiple AI agents and integrates with various platforms for automated content creation and distribution across social media, email, voice, and team communication channels.

---

**🎯 Perfect for**: Content creators, marketing teams, businesses, and developers who want to automate their content distribution across multiple channels with AI-powered generation and optimization.