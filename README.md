<<<<<<< HEAD
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
=======
# The Lab Verse Monitoring Stack 🚀

A comprehensive, production-ready monitoring infrastructure with **AI-powered project management** through Kimi Instruct - your hybrid AI project manager.

## 🤖 What is Kimi Instruct?

**Kimi Instruct** is a revolutionary hybrid AI project manager that combines artificial intelligence with human oversight to manage your entire monitoring infrastructure project. Think of it as having a senior technical PM who never sleeps, always remembers context, and can execute tasks autonomously while keeping you in the loop.

### ✨ Key Features

- **🧠 AI-Powered Task Management**: Automatically creates, prioritizes, and executes tasks
- **👥 Human-AI Collaboration**: Smart approval workflows for critical decisions
- **📊 Real-time Project Tracking**: Live progress monitoring and risk assessment
- **💰 Budget Intelligence**: Automated cost tracking and optimization recommendations
- **🚨 Smart Escalation**: Intelligent issue escalation based on severity and impact
- **📈 Predictive Analytics**: ML-powered insights for project success
- **🔄 Self-Healing Operations**: Automatic detection and resolution of common issues
- **📱 Multi-Interface Access**: Web dashboard, CLI, and API interfaces

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    🤖 Kimi Instruct                        │
│                 AI Project Manager                         │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │   Web UI    │ │     CLI      │ │        API          │  │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Monitoring Stack                            │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │ Prometheus  │ │   Grafana    │ │   AlertManager      │  │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key (optional but recommended for AI features)

### 1. Clone the Repository
```bash
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-
```

### 2. Install Kimi Instruct
```bash
# Make the installation script executable
chmod +x scripts/install-kimi.sh

# Run the installation
./scripts/install-kimi.sh
```

### 3. Set Environment Variables (Optional)
```bash
# For enhanced AI capabilities
export OPENAI_API_KEY="your-openai-api-key"

# For Slack notifications
export SLACK_WEBHOOK_URL="your-slack-webhook-url"
```

### 4. Start the Stack
```bash
docker-compose up -d
```

### 5. Access Kimi Dashboard
Open your browser and navigate to: **http://localhost:8084/dashboard**

## 📱 Using Kimi Instruct

### Web Dashboard
Access the intuitive web interface at `http://localhost:8084/dashboard` to:
- Monitor project progress in real-time
- View task status and completion metrics
- Review budget and timeline information
- Approve or deny tasks requiring human input
- Get AI-powered recommendations

### Command Line Interface
```bash
# Check project status
./kimi-cli status

# Create a new task
./kimi-cli task --title "Deploy new service" --priority high

# List all tasks
./kimi-cli list

# Run optimization analysis
./kimi-cli optimize

# Perform human checkin
./kimi-cli checkin

# Generate comprehensive report
./kimi-cli report
```

### HTTP API
```bash
# Get project status
curl http://localhost:8084/status

# Create a task
curl -X POST http://localhost:8084/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Monitor deployment", "priority": "high"}'

# Get next recommended actions
curl http://localhost:8084/next-actions
```

## 🎯 What Kimi Can Do For You

### Autonomous Operations
- **Deployment Management**: Automatically deploy services to staging/production
- **Cost Optimization**: Continuously analyze and optimize infrastructure costs
- **Health Monitoring**: Perform regular health checks across all services
- **Backup Management**: Ensure data backup procedures are followed
- **Security Updates**: Apply security patches and updates automatically

### Human-AI Collaboration
- **Production Deployments**: Requests approval for production changes
- **Budget Decisions**: Seeks approval for expenditures over $1,000
- **Architecture Changes**: Involves humans in major technical decisions
- **Risk Mitigation**: Escalates high-risk situations immediately

### Intelligence & Insights
- **Predictive Analytics**: Forecasts project completion and potential issues
- **Resource Optimization**: Recommends optimal resource allocation
- **Performance Trends**: Identifies performance patterns and anomalies
- **Cost Intelligence**: Provides detailed cost analysis and savings opportunities

## 📊 Monitoring Stack Components

| Component | Port | Purpose | Managed by Kimi |
|-----------|------|---------|------------------|
| **Kimi Dashboard** | 8084 | AI Project Manager Interface | ✅ Self-managed |
| **Prometheus** | 9090 | Metrics Collection | ✅ Auto-configured |
| **Grafana** | 3000 | Visualization & Dashboards | ✅ Auto-configured |
| **AlertManager** | 9093 | Alert Management | ✅ Auto-configured |
| **Node Exporter** | 9100 | System Metrics | ✅ Auto-monitored |

## 🔧 Configuration

### Kimi Configuration
Edit `config/kimi_instruct.json` to customize:
- Human oversight mode (collaborative/autonomous)
- Risk thresholds and escalation rules
- Project objectives and constraints
- Budget and timeline settings
- Decision authority levels

### Example Configuration
```json
{
  "human_oversight_mode": "collaborative",
  "auto_execution_threshold": 0.75,
  "risk_thresholds": {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8
  },
  "decision_authority": {
    "auto_deploy_staging": true,
    "auto_deploy_production": false,
    "auto_cost_optimization": true
  }
}
```

## 📈 Project Metrics

Kimi tracks comprehensive project metrics:

- **Progress**: Task completion percentage
- **Budget**: Remaining budget and burn rate
- **Timeline**: Days remaining and milestone tracking
- **Risk**: Real-time risk assessment and mitigation
- **Quality**: Code quality and deployment success rates
- **Team**: Human intervention frequency and efficiency

## 🚨 Alerts & Notifications

Kimi provides intelligent alerting:
- **Budget Alerts**: When 75%, 90%, 95% of budget is consumed
- **Timeline Alerts**: When project is at risk of missing deadlines
- **Technical Alerts**: When critical systems are down or degraded
- **Human Approval**: When decisions require human oversight
- **Progress Updates**: Daily/weekly progress summaries

## 🔄 Workflow Examples

### Typical Day with Kimi
1. **Morning**: Kimi provides daily status report
2. **Continuous**: Monitors all systems and metrics
3. **Proactive**: Identifies and resolves issues automatically
4. **Collaborative**: Requests approval for critical decisions
5. **Evening**: Summarizes progress and plans tomorrow's tasks

### Deployment Workflow
1. Kimi detects code changes requiring deployment
2. Automatically deploys to staging environment
3. Runs automated tests and quality checks
4. Requests human approval for production deployment
5. Deploys to production upon approval
6. Monitors deployment health and performance
7. Reports success metrics and any issues

## 🛠️ Development

### Running Tests
```bash
# Run Kimi integration tests
python -m pytest tests/test_kimi_integration.py -v

# Run all tests
python -m pytest tests/ -v
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.kimi.txt

# Run Kimi service locally
python -m src.kimi_instruct.service

# Use CLI directly
python -m src.kimi_instruct.cli status
>>>>>>> origin/feat/ai-connectivity-layer
```

## 🤝 Contributing

<<<<<<< HEAD
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
=======
We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📚 Documentation

- **API Documentation**: http://localhost:8084/docs (when running)
- **Configuration Guide**: See `config/kimi_instruct.json`
- **CLI Reference**: `./kimi-cli --help`
- **Architecture Deep Dive**: See `docs/` directory

## 🆘 Troubleshooting

### Common Issues

**Kimi not responding?**
```bash
# Check service status
./check-kimi

# View logs
docker-compose logs kimi-project-manager

# Restart service
docker-compose restart kimi-project-manager
```

**Tasks not executing?**
- Check if OpenAI API key is set (for AI features)
- Verify network connectivity between services
- Review task dependencies and approval requirements

**Dashboard not loading?**
- Ensure port 8084 is not blocked
- Check Docker container health status
- Verify browser allows localhost connections

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with love for the developer community
- Powered by cutting-edge AI technology
- Inspired by the need for intelligent infrastructure management

---

**🎯 Ready to revolutionize your monitoring infrastructure?**

Kimi Instruct represents the future of infrastructure management - where AI and human intelligence work together to build, monitor, and optimize your systems. Start your journey today!

```bash
./scripts/install-kimi.sh
docker-compose up -d
# Visit http://localhost:8084/dashboard
```

**Your monitoring stack now has an AI project manager! 🚀**
>>>>>>> origin/feat/ai-connectivity-layer
