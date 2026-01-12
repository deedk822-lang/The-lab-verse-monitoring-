# PR #1152 Setup Instructions

## Overview
This PR replaces Anthropic with Z.ai (GLM-4.7) and Perplexity (Sonar Pro).

## Prerequisites

### 1. Z.ai Account Setup
1. Sign up at https://api.z.ai
2. **CRITICAL**: Recharge your account or purchase a resource package
3. Get your API key from https://api.z.ai/console
4. Current error: `HTTP 429 - Insufficient balance`

### 2. Perplexity Account Setup
1. Sign up at https://www.perplexity.ai
2. Go to Settings → API
3. Generate an API key
4. Note: Free tier has rate limits

## Local Setup

```bash
# 1. Install dependencies
pip install openai python-dotenv requests

# 2. Create .env file
cp .env.example .env

# 3. Add your API keys to .env
# ZAI_API_KEY=your_actual_key
# PERPLEXITY_API_KEY=your_actual_key

# 4. Test environment
python validate_env.py

# 5. Test AI workflow
python scripts/test_brain.py
```

## Vercel Deployment

### Add secrets to Vercel:
```bash
vercel secrets add zai-api-key "your_zai_key"
vercel secrets add perplexity-api-key "your_perplexity_key"
```

Or via Vercel Dashboard:
1. Go to Project Settings → Environment Variables
2. Add `ZAI_API_KEY` → Reference secret `zai-api-key`
3. Add `PERPLEXITY_API_KEY` → Reference secret `perplexity-api-key`

## GitHub Actions Setup

### Add secrets to GitHub:
1. Go to Repository Settings → Secrets and variables → Actions
2. Add `ZAI_API_KEY`
3. Add `PERPLEXITY_API_KEY`

## Troubleshooting

### Z.ai Error 429: Insufficient Balance
**Problem**: Account has no credits or resource package
**Solution**:
1. Go to https://api.z.ai/console
2. Purchase credits or resource package
3. Wait for activation (usually instant)
4. Re-run validation

### Perplexity Error 429: Rate Limit
**Problem**: Exceeded free tier rate limits
**Solution**:
1. Wait 60 seconds before retrying
2. Consider upgrading to paid plan
3. Check limits at https://www.perplexity.ai/settings/api

### Validation Still Failing
```bash
# Check API keys are set
echo $ZAI_API_KEY
echo $PERPLEXITY_API_KEY

# Test manually
python -c "from openai import OpenAI; print(OpenAI(api_key='test').base_url)"

# Enable debug logging
export OPENAI_LOG=debug
python validate_env.py
```

## API Endpoints

- **Z.ai**: `https://api.z.ai/api/paas/v4/`
- **Perplexity**: `https://api.perplexity.ai`

## Models

- **Z.ai**: `glm-4.7` (reasoning)
- **Perplexity**: `sonar-pro` (research)
