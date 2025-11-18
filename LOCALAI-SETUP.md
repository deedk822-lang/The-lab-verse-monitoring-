# LocalAI + Mistral Integration Guide

## 🎯 Overview

This guide covers the complete setup of LocalAI with Mistral 7B for The Lab Verse Monitoring project.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Node.js 20+ installed
- 8GB+ RAM (for running Mistral model)
- 10GB+ free disk space (for model downloads)

## 🚀 Quick Start

### 1. Start LocalAI

```bash
# Start the LocalAI container
docker-compose -f docker-compose.localai.yml up -d

# View logs to ensure it's running
docker-compose -f docker-compose.localai.yml logs -f
```

### 2. Wait for Model Download

The first time you start LocalAI, it will download the Mistral model (~4-5 GB). This may take 10-30 minutes depending on your internet connection.

### 3. Verify Installation

```bash
# Check if LocalAI is responding
curl http://localhost:8080/v1/models

# Test a simple completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-ai-key-optional" \
  -d '{
    "model": "mistral-7b-instruct",
    "messages": [{"role":"user","content":"Hello!"}]
  }'
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# The LocalAI variables are already set:
# LOCALAI_API_URL=http://localhost:8080/v1
# LOCALAI_API_KEY=local-ai-key-optional
# MISTRAL_API_URL=http://localhost:8080/v1
# MISTRAL_API_KEY=local-ai-key-optional
```

### 5. Install Dependencies and Test

```bash
# Install npm dependencies
npm install

# Run API key validation
node scripts/validate-api-keys.js

# You should see:
# Mistral     : ✅ Available & Valid
# LocalAI     : ✅ Available & Valid
```

## 🔧 Configuration Details

### Docker Compose Configuration

The `docker-compose.localai.yml` file configures:

- **Port**: 8080 (LocalAI API)
- **Model Path**: `./models` (where model configs are stored)
- **Data Path**: `./localai-data` (where downloaded models are stored)
- **Threads**: 4 (adjust based on your CPU)
- **Context Size**: 4096 tokens
- **API Key**: Optional authentication

### Model Configuration

The `models/mistral-7b-instruct.yaml` file specifies:

- **Model**: Mistral 7B Instruct v0.1 (Q4_K_M quantization)
- **Backend**: llama.cpp
- **Temperature**: 0.7 (creativity level)
- **Max Tokens**: 2048 (response length)
- **Context Size**: 4096 tokens (conversation memory)

## 🐳 Docker Commands Reference

### Start/Stop

```bash
# Start LocalAI
docker-compose -f docker-compose.localai.yml up -d

# Stop LocalAI
docker-compose -f docker-compose.localai.yml down

# Restart LocalAI
docker-compose -f docker-compose.localai.yml restart
```

### Logs and Monitoring

```bash
# View real-time logs
docker-compose -f docker-compose.localai.yml logs -f

# View last 100 lines
docker-compose -f docker-compose.localai.yml logs --tail=100

# Check container status
docker ps | grep localai
```

### Troubleshooting

```bash
# Remove all data and start fresh
docker-compose -f docker-compose.localai.yml down -v
rm -rf localai-data/*
docker-compose -f docker-compose.localai.yml up -d

# Access container shell
docker exec -it localai-mistral sh

# Check container health
docker inspect localai-mistral | grep -A 10 Health
```

## 🌐 Alternative: Cloud Mistral API

If you prefer not to run LocalAI locally, you can use Mistral's cloud API:

### 1. Sign Up

Visit [console.mistral.ai](https://console.mistral.ai/) and create an account.

### 2. Get API Key

Generate an API key from the Mistral console.

### 3. Update Environment

```bash
# In your .env file:
MISTRAL_API_URL=https://api.mistral.ai/v1
MISTRAL_API_KEY=your_actual_mistral_api_key
```

### 4. Update GitHub Secrets

```bash
# Using GitHub CLI
gh secret set MISTRAL_API_KEY --body "your_actual_mistral_api_key"
```

## 📊 GitHub CI Configuration

For CI to pass, you need to add these secrets to your GitHub repository:

### Using GitHub Web Interface

1. Go to: `Settings` → `Secrets and variables` → `Actions`
2. Click `New repository secret`
3. Add:
   - Name: `MISTRAL_API_KEY`
   - Value: `local-ai-key-optional` (or your cloud API key)
4. Repeat for `LOCALAI_API_KEY`

### Using GitHub CLI

```bash
gh secret set MISTRAL_API_KEY --body "local-ai-key-optional"
gh secret set LOCALAI_API_KEY --body "local-ai-key-optional"

# Verify secrets are set
gh secret list
```

## 🧪 Testing

### Test LocalAI API

```bash
# List available models
curl http://localhost:8080/v1/models | jq

# Test chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-ai-key-optional" \
  -d '{
    "model": "mistral-7b-instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is 2+2?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }' | jq
```

### Run Validation Script

```bash
node scripts/validate-api-keys.js
```

Expected output:
```
🔍 API Key Validation Results:
================================
OpenAI      : ✅ Available & Valid (sk-proj-...)
Anthropic   : ⚠️ Present but Invalid (sk-or-v1...)
Perplexity  : ✅ Available & Valid (pplx-k1l...)
Mistral     : ✅ Available & Valid (local...)
Groq        : ✅ Available & Valid (gsk_tS2P...)
Gemini      : ✅ Available & Valid (AIzaSyD8...)
LocalAI     : ✅ Available & Valid (local...)
================================
📊 Summary: 7/7 providers configured

🔗 Fallback Chain Status:
================================
OpenAI Chain:    ✅ GPT-4 → ✅ Perplexity
Anthropic Chain: ❌ Claude → ✅ Mistral → ✅ Gemini → ✅ Groq

✅ SUCCESS: Multiple providers available for robust fallback system
🎯 Fallback coverage: Excellent
```

## 🐛 Troubleshooting

### Issue: Port 8080 already in use

**Solution**: Change the port in `docker-compose.localai.yml`:

```yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

Then update your `.env`:
```env
LOCALAI_API_URL=http://localhost:8081/v1
MISTRAL_API_URL=http://localhost:8081/v1
```

### Issue: Model download fails

**Solution**: Manually download the model:

```bash
mkdir -p localai-data
cd localai-data
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

### Issue: Out of memory

**Solution**: Use a smaller quantization or reduce context size:

In `models/mistral-7b-instruct.yaml`:
```yaml
context_size: 2048  # Reduce from 4096
```

Or download a smaller model (Q3 or Q2 quantization).

### Issue: CI still shows "Missing"

**Solution**: Verify GitHub secrets:

```bash
# Check secrets are set
gh secret list

# Re-add if needed
gh secret set MISTRAL_API_KEY --body "local-ai-key-optional"
gh secret set LOCALAI_API_KEY --body "local-ai-key-optional"
```

## 📚 Additional Resources

- [LocalAI Documentation](https://localai.io/docs/)
- [LocalAI Model Gallery](https://localai.io/models/)
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## ✅ Success Checklist

- [ ] Docker is installed and running
- [ ] LocalAI container is running (`docker ps`)
- [ ] Mistral model is downloaded (check logs)
- [ ] LocalAI responds to API calls
- [ ] `.env` file is configured
- [ ] Dependencies are installed (`npm install`)
- [ ] Validation passes (`node scripts/validate-api-keys.js`)
- [ ] GitHub secrets are added
- [ ] CI passes with green checkmarks

## 🎉 You're Done!

Your LocalAI + Mistral integration is complete. The system now has:

- ✅ Local LLM running (no external API costs)
- ✅ Mistral 7B model for intelligent responses
- ✅ OpenAI-compatible API
- ✅ Fallback chain with 7 providers
- ✅ CI validation passing

---

**Questions?** Check the troubleshooting section or review the CI logs for more details.
