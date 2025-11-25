# Mistral & LocalAI Setup Guide for Lab Verse Monitoring

## 🎯 Overview

This guide helps you set up Mistral and LocalAI with your Lab Verse Monitoring project, enabling local AI inference with fallback chains and MCP server integration.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Node.js 20+ (already in project)
- Python 3.12+ (for MCP server)
- Git
- ~6GB free disk space for Mistral model

## 🚀 Quick Start

### 1. Start LocalAI with Mistral

```bash
# Start LocalAI container with Mistral model
docker compose up -d localai

# Wait for model to download (first time only)
echo "Waiting for LocalAI to be ready..."
timeout 300 bash -c 'until curl -s http://localhost:8080/v1/models | grep hermes; do sleep 5; echo "Still downloading model..."; done'

echo "✅ LocalAI is ready!"
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env

# Add these lines to your .env file:
LOCALAI_API_URL=http://localhost:8080/v1
LOCALAI_API_KEY=localai-key
MISTRAL_API_URL=http://localhost:8080/v1
MISTRAL_API_KEY=localai-key
```

### 3. Test the Setup

```bash
# Run the integration test
node test-mistral-localai.js
```

## 📝 Detailed Setup

### LocalAI Configuration

#### Docker Compose Setup

The `docker-compose.yml` includes:
- **LocalAI container**: OpenAI-compatible API server
- **Health checks**: Automatic monitoring
- **Model mounting**: Models stored in `./models/` directory

#### Model Configuration

The Mistral model is configured via `models/hermes-2-pro-mistral.yaml`:
```yaml
name: hermes-2-pro-mistral
parameters:
  model: huggingface/NousResearch/Hermes-2-Pro-Mistral-7B-GGUF
  temperature: 0.7
  top_p: 0.9
  max_tokens: 2048
```

### MCP Server Setup

#### Install and Run MCP Server

```bash
# Run the setup script
cd mcp-server
./setup.sh

# Start the server
./start_server.py
```

#### Environment Configuration

Add these to your `.env`:
```bash
MCP_SERVER_URL=http://localhost:8000
CONNECTOR_MOD=cdata.postgresql
CONNECTION_STRING=Server=host.docker.internal;Port=5432;Database=mydb;User Id=myuser;Password=mypass;
```

## 🔧 Configuration Details

### Provider Configuration

The `src/config/providers.js` file includes:

```javascript
// Mistral via LocalAI (high priority)
'mistral': {
  model: process.env.MISTRAL_API_KEY ?
    createOpenAI({
      baseURL: process.env.MISTRAL_API_URL || 'http://localhost:8080/v1',
      apiKey: process.env.MISTRAL_API_KEY
    })('hermes-2-pro-mistral') : null,
  priority: 3,
  enabled: !!(process.env.MISTRAL_API_URL && process.env.MISTRAL_API_KEY),
  name: 'Mistral (LocalAI)',
  category: 'anthropic-fallback'
},

// LocalAI generic (fallback)
'mistral-local': {
  model: (process.env.LOCALAI_HOST || process.env.LOCALAI_API_KEY) ?
    createOpenAI({
      baseURL: process.env.LOCALAI_HOST || 'http://localhost:8080/v1',
      apiKey: process.env.LOCALAI_API_KEY || 'localai'
    })('hermes-2-pro-mistral') : null,
  priority: 10,
  enabled: !!(process.env.LOCALAI_HOST || process.env.LOCALAI_API_KEY),
  name: 'Mistral Local',
  category: 'local'
}
```

### Fallback Chain Priority

1. **OpenAI GPT-4** (priority 1)
2. **Perplexity** (priority 2) 
3. **Mistral (LocalAI)** (priority 3) ⭐ *NEW*
4. **Gemini Pro** (priority 5)
5. **Groq Llama** (priority 6)
6. **Mistral Local** (priority 10) ⭐ *NEW*

## 🧪 Testing

### Individual Component Tests

```bash
# Test LocalAI directly
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer localai-key" \
  -d '{
    "model": "hermes-2-pro-mistral",
    "messages": [{"role":"user","content":"Hello!"}],
    "max_tokens": 50
  }'

# Test provider configuration
node -e "
import('./src/config/providers.js').then(({ providers }) => {
  Object.entries(providers).forEach(([k, v]) => {
    console.log(\`\${k}: \${v.enabled ? '✅' : '❌'} - \${v.name}\`);
  });
});
"

# Test MCP server health
curl http://localhost:8000/health
```

### Integration Test

```bash
# Run full integration test
node test-mistral-localai.js
```

Expected output:
```
🔍 Testing Mistral & LocalAI Integration

1️⃣ Testing LocalAI connection...
   ✅ LocalAI models loaded: hermes-2-pro-mistral
   ✅ LocalAI response: Hello there!

2️⃣ Testing Mistral provider...
   ✅ Mistral response: 4

3️⃣ Testing MCP Server...
   ✅ MCP Server health: ✅ MCP Server is healthy

4️⃣ Testing Provider Configuration...
   🔧 Available providers:
      gpt-4: ❌ (GPT-4)
      perplexity: ✅ (Perplexity)
      mistral: ✅ (Mistral (LocalAI))
      gemini-pro: ❌ (Gemini Pro)
      groq-llama: ✅ (Groq Llama)
      mistral-local: ✅ (Mistral Local)
   ✅ Active provider found: Mistral (LocalAI)

📊 Test Results Summary:
   LocalAI: ✅ PASS
   Mistral: ✅ PASS
   MCP Server: ✅ PASS
   Provider Config: ✅ PASS

🎉 All tests passed! Your Mistral & LocalAI setup is working correctly.
```

## 🔧 Troubleshooting

### Common Issues

#### LocalAI Not Starting
```bash
# Check Docker logs
docker logs localai

# Check if port is available
netstat -tlnp | grep 8080

# Restart container
docker compose restart localai
```

#### Model Not Loading
```bash
# Check model files
ls -la models/

# Verify model configuration
cat models/hermes-2-pro-mistral.yaml

# Check model download progress
docker logs localai | grep -i model
```

#### Connection Refused
```bash
# Verify LocalAI is running
curl http://localhost:8080/v1/models

# Check environment variables
env | grep -E "(LOCALAI|MISTRAL)"

# Test with different API key
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer localai-key" \
  -d '{"model":"hermes-2-pro-mistral","messages":[{"role":"user","content":"test"}]}'
```

#### MCP Server Issues
```bash
# Check Python version
python3 --version

# Verify dependencies
source mcp-server/.venv/bin/activate
pip list | grep mcp

# Test connection manually
python3 -c "
from cdata.postgresql import connect
print('✅ Connector available')
"
```

### Performance Optimization

#### Model Loading
- Model downloads once (~6GB) and caches locally
- Subsequent starts are much faster
- Consider SSD for better performance

#### Resource Allocation
```yaml
# In docker-compose.yml, adjust for your system:
localai:
  deploy:
    resources:
      limits:
        memory: 8G
        cpus: '4'
      reservations:
        memory: 4G
        cpus: '2'
```

#### Batch Requests
```javascript
// Use streaming for better performance
const stream = await localai.chat.completions.create({
  model: "hermes-2-pro-mistral",
  messages: [{ role: "user", content: "Generate a long response" }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and deploy
docker compose -f docker-compose.prod.yml up -d

# Scale LocalAI for load
docker compose up -d --scale localai=3
```

### Environment Variables for Production
```bash
# Security
LOCALAI_API_KEY=your-secure-api-key
MISTRAL_API_KEY=your-secure-api-key

# Performance
LOCALAI_API_URL=https://your-domain.local/v1
MISTRAL_API_URL=https://your-domain.local/v1

# Monitoring
MCP_SERVER_URL=https://mcp.your-domain.com
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
- name: Start LocalAI
  run: |
    docker compose up -d localai
    timeout 300 bash -c 'until curl -s http://localhost:8080/v1/models; do sleep 5; done'

- name: Test Integration
  run: |
    cp .env.example .env
    echo "LOCALAI_API_URL=http://localhost:8080/v1" >> .env
    echo "MISTRAL_API_URL=http://localhost:8080/v1" >> .env
    echo "LOCALAI_API_KEY=localai-key" >> .env
    echo "MISTRAL_API_KEY=localai-key" >> .env
    node test-mistral-localai.js
```

## 📊 Monitoring

### Health Checks
```bash
# LocalAI health
curl http://localhost:8080/v1/models

# MCP server health  
curl http://localhost:8000/health

# Application health
curl http://localhost:3000/api/health
```

### Metrics
```javascript
// Add to your monitoring
const metrics = {
  localai_requests: 0,
  mistral_requests: 0,
  mcp_queries: 0,
  errors: 0,
};

// Track usage
const startTiming = Date.now();
const response = await localai.chat.completions.create({...});
const latency = Date.now() - startTiming;

metrics.localai_requests++;
// send to your metrics system
```

## 🎯 Next Steps

1. **Custom Models**: Add more models to `./models/`
2. **GPU Acceleration**: Configure LocalAI with GPU support
3. **Load Balancing**: Set up multiple LocalAI instances
4. **Monitoring**: Integrate with your monitoring system
5. **Security**: Implement API key rotation and rate limiting

## 📞 Support

- **LocalAI Documentation**: https://localai.io/docs/
- **MCP Documentation**: https://modelcontextprotocol.io/
- **Project Issues**: https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues

---

🎉 **Congratulations!** You now have a fully functional Mistral & LocalAI setup with MCP integration for your Lab Verse Monitoring project!