# AI Content Creation Suite

A comprehensive fullstack JavaScript application that replicates n8n content creation workflows with support for multiple AI providers including OpenAI, Google Gemini, LocalAI, and Z.AI GLM-4.6.

## 🚀 Features

### Multi-Provider AI Support
- **OpenAI**: GPT-4, DALL-E, Whisper, TTS
- **Google Gemini**: Advanced reasoning, Imagen, Veo, Google Search/Maps integration
- **LocalAI**: Privacy-focused local inference with various models
- **Z.AI GLM-4.6**: Efficient reasoning, tool use, long context (200K tokens)

### Content Generation
- **Text**: Articles, blog posts, social media content
- **Images**: High-quality generation with aspect ratio control
- **Videos**: Prompt-based video generation and animation
- **Audio**: Text-to-speech and speech-to-text
- **Multimodal**: Combined content types with integrated workflows

### Advanced Features
- Real-time progress tracking with WebSockets
- SEO optimization and metadata generation
- Social media post generation for multiple platforms
- Cost tracking and usage analytics
- Caching with Redis for improved performance
- Rate limiting and API key authentication
- Docker support for easy deployment

## 🛠️ Quick Start

### Prerequisites
- Node.js 18+ 
- Redis (optional, for caching)
- Docker & Docker Compose (for containerized deployment)

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd ai-content-creation-suite
npm run setup
```

2. **Configure API keys in `.env`:**
```bash
# At least one provider is required
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ZAI_API_KEY=your_zai_key
LOCALAI_URL=http://localhost:8080

# Authentication
API_KEY=your_secure_api_key
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
|----------|-------------|---------|
| `PORT` | Server port | 3000 |
| `NODE_ENV` | Environment | development |
| `API_KEY` | API authentication key | - |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GOOGLE_API_KEY` | Google AI API key | - |
| `ZAI_API_KEY` | Z.AI API key | - |
| `LOCALAI_URL` | LocalAI server URL | http://localhost:8080 |

### Provider Configuration

Each provider can be configured with specific models and capabilities:

```javascript
// Example: Google Gemini with thinking mode
const result = await contentGenerator.generateContent({
  topic: "AI in Healthcare",
  audience: "medical professionals", 
  tone: "professional",
  mediaType: "text",
  provider: "google",
  options: {
    thinkingMode: true,
    model: "gemini-1.5-pro"
  }
});
```

## 📚 API Reference

### Generate Content
```http
POST /api/content/generate
Content-Type: application/json
x-api-key: your-api-key

{
  "topic": "Artificial Intelligence",
  "audience": "developers",
  "tone": "professional",
  "mediaType": "text",
  "provider": "google",
  "keywords": ["AI", "machine learning"],
  "length": "medium"
}
```

### Test Providers
```http
GET /api/test/providers
```

### Health Check
```http
GET /health
```

## 🏗️ Architecture

```
src/
├── config/           # Provider configurations
├── middleware/       # Authentication, caching, error handling
├── routes/          # API endpoints
├── services/        # AI providers and content generation
├── utils/           # Logging, Redis, utilities
└── server.js        # Main application entry point

public/
├── index.html       # Web UI
└── js/
    └── app.js       # Frontend JavaScript
```

## 🔌 Provider Integration

### Google Gemini Features
- Real-time web search integration
- Google Maps data integration
- Imagen for image generation
- Veo for video generation
- Advanced reasoning with thinking mode

### Z.AI GLM-4.6 Features
- Tool use and agentic workflows
- Long context processing (200K tokens)
- Streaming responses
- Cost-efficient processing

### LocalAI Features
- Privacy-focused local inference
- Model downloading and management
- Custom model support
- Offline capability

## 🧪 Testing

```bash
# Test all providers
npm test

# Test specific functionality
curl http://localhost:3000/api/test/health
```

## 📊 Monitoring

The application includes comprehensive logging and monitoring:

- **Winston** for structured logging
- **Redis** for caching and session management
- **Health checks** for all providers
- **Cost tracking** for API usage
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

3. **Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
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

## 🔄 Updates

### Recent Updates
- Added Z.AI GLM-4.6 integration
- Enhanced Google Gemini features
- Improved LocalAI support
- Added multimodal content generation
- Enhanced WebSocket real-time updates

### Roadmap
- [ ] Advanced analytics dashboard
- [ ] Custom model fine-tuning
- [ ] Batch processing capabilities
- [ ] Advanced workflow automation
- [ ] Multi-language UI support