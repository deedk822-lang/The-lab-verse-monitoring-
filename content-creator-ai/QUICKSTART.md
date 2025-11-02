# Quick Start Guide 🚀

Get up and running with Content Creator AI in 5 minutes!

## Prerequisites

- Node.js 18+ installed
- At least one AI provider API key (Google, OpenAI, or Z.AI)

## Step 1: Install Dependencies

```bash
cd content-creator-ai
npm install
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimum required configuration**:
```env
# Choose your primary provider and add its API key:

# Option 1: Google Gemini (Recommended for beginners)
GOOGLE_API_KEY=your-google-api-key-here
DEFAULT_PROVIDER=google

# Option 2: OpenAI
OPENAI_API_KEY=sk-your-openai-key
DEFAULT_PROVIDER=openai

# Option 3: Z.AI (Cost-efficient)
ZAI_API_KEY=your-zai-key
DEFAULT_PROVIDER=zai

# Set a secure API key for your webhook
API_KEY=change-this-to-something-secure
```

### Getting API Keys

- **Google AI Studio**: https://makersuite.google.com/app/apikey
- **OpenAI**: https://platform.openai.com/api-keys
- **Z.AI**: https://bigmodel.cn/ (Sign up and get API key)

## Step 3: Start the Server

```bash
npm start
```

You should see:
```
🚀 Content Creator AI Server Started
Server running on: http://localhost:3000
```

## Step 4: Test It Out!

### Option A: Web Interface (Easiest)

1. Open your browser: http://localhost:3000
2. Fill out the form:
   - Topic: "The benefits of AI"
   - Media Type: "Text Article"
   - Click "Generate Content"
3. Watch the progress and see your content!

### Option B: API Request (For developers)

```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "topic": "The benefits of AI",
    "media_type": "text",
    "provider": "auto",
    "tone": "professional",
    "length": "medium"
  }'
```

### Option C: Test Without Real APIs

Try the test endpoint first (no API keys needed):

```bash
curl http://localhost:3000/api/test
```

Or visit: http://localhost:3000/api/test in your browser

## Step 5: Optional Enhancements

### Enable Caching (Recommended for Production)

1. Install Redis:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

2. Update .env:
```env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
```

### Add LocalAI (Free, Self-Hosted)

1. Run LocalAI:
```bash
# Quick start with Docker
docker run -p 8080:8080 --name localai localai/localai:latest-aio-cpu

# Or download binary
curl https://localai.io/install.sh | sh
local-ai run llama-3.2-1b-instruct
```

2. Update .env:
```env
LOCALAI_ENABLED=true
LOCALAI_URL=http://localhost:8080
```

3. Test LocalAI provider:
```bash
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "topic": "Hello world",
    "media_type": "text",
    "provider": "localai",
    "length": "short"
  }'
```

## Common Use Cases

### Generate a Blog Post

```json
{
  "topic": "Top 10 JavaScript frameworks in 2024",
  "media_type": "text",
  "length": "long",
  "tone": "professional",
  "include_seo": true,
  "include_social": true
}
```

### Create Social Media Content

```json
{
  "topic": "New product launch announcement",
  "media_type": "text",
  "length": "short",
  "tone": "friendly",
  "include_social": true
}
```

### Generate an Image

```json
{
  "topic": "Futuristic city skyline at sunset",
  "media_type": "image",
  "provider": "google",
  "aspect_ratio": "16:9",
  "style": "photorealistic"
}
```

### Research and Summarize

```json
{
  "topic": "Latest developments in quantum computing",
  "media_type": "text",
  "provider": "google",
  "enable_research": true,
  "length": "medium"
}
```

### Use Z.AI Thinking Mode

```json
{
  "topic": "Explain the Byzantine Generals Problem",
  "media_type": "text",
  "provider": "zai",
  "thinking_mode": true,
  "length": "medium"
}
```

## Monitoring

### Check Server Health

```bash
curl http://localhost:3000/api/health
```

### View Usage Statistics

```bash
curl -H "X-API-Key: your-api-key" http://localhost:3000/api/stats
```

### Check Logs

```bash
tail -f logs/combined.log
```

## Troubleshooting

### Server won't start

1. Check if port 3000 is available:
```bash
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows
```

2. Try a different port:
```env
PORT=8080
```

### "No AI providers enabled" error

- Make sure you've set at least one API key in `.env`
- Verify the API key is correct
- Check the provider is enabled

### API requests fail

1. Verify your API key is correct:
```bash
curl -H "X-API-Key: wrong-key" http://localhost:3000/api/test
# Should return 403 Forbidden
```

2. Check if the provider is working:
```bash
curl http://localhost:3000/api/health
```

## Next Steps

- Read the full [README.md](./README.md) for advanced features
- Explore different providers and compare results
- Set up monitoring and analytics
- Deploy to production (see Deployment section in README)
- Integrate with your applications via the API

## Need Help?

- Check the logs: `tail -f logs/combined.log`
- Visit: http://localhost:3000/api/health
- Review the [README.md](./README.md) for detailed documentation

---

Happy content creating! 🎉
