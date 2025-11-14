# MCP Gateway Setup Guide

## 📋 Overview

This guide covers setting up your MCP (Model Context Protocol) gateway servers for:
- **HuggingFace**: Models, datasets, spaces, and inference
- **SocialPilot**: Social media scheduling and analytics
- **Unito**: Two-way sync between 60+ tools
- **WordPress.com**: Blog post management

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Navigate to mcp-server directory
cd mcp-server

# Install required packages
npm install @modelcontextprotocol/sdk dotenv
```

### 2. Configure Environment Variables

Create `.env` file in `mcp-server/`:

```bash
# Gateway Configuration
GATEWAY_URL=https://the-lab-verse-monitoring.vercel.app
GATEWAY_KEY=your-gateway-api-key-here

# HuggingFace
HF_API_TOKEN=hf_xxxxxxxxxxxxx

# SocialPilot
SOCIALPILOT_ACCESS_TOKEN=sp_xxxxxxxxxxxxx

# Unito
UNITO_ACCESS_TOKEN=unito_xxxxxxxxxxxxx

# WordPress.com
WORDPRESS_COM_OAUTH_TOKEN=wpcom_xxxxxxxxxxxxx
```

### 3. Start Gateway Servers

```bash
# HuggingFace Gateway
node huggingface-gateway.js

# SocialPilot Gateway
node socialpilot-gateway.js

# Unito Gateway
node unito-gateway.js

# WordPress.com Gateway
node wpcom-gateway.js
```

---

## 🔧 Configuration Details

### Gateway URL Priority

The gateway URL is determined in this order:

1. `GATEWAY_URL` environment variable
2. `VERCEL_URL` (auto-set in Vercel deployments)
3. Fallback: `http://localhost:3000`

### Authentication Tokens

Each gateway requires an authentication token:

| Service | Primary Env Var | Fallback Env Var |
|---------|----------------|------------------|
| **Gateway** | `GATEWAY_KEY` | Service-specific token |
| **HuggingFace** | `HF_API_TOKEN` | `GATEWAY_KEY` |
| **SocialPilot** | `SOCIALPILOT_ACCESS_TOKEN` | `GATEWAY_KEY` |
| **Unito** | `UNITO_ACCESS_TOKEN` | `GATEWAY_KEY` |
| **WordPress.com** | `WORDPRESS_COM_OAUTH_TOKEN` | `GATEWAY_KEY` |

---

## 📦 Main Gateway Endpoint Setup

### File Structure

```
pages/
└── api/
    └── gateway/
        └── v1/
            └── chat/
                └── completions.js  ← Main gateway endpoint
```

### Required Environment Variables

Add to Vercel (or `.env.local`):

```bash
# Authentication
GATEWAY_API_KEY=your-secure-key-here
API_SECRET_KEY=fallback-key-here

# OpenTelemetry (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-otel-endpoint
```

### Testing the Gateway

```bash
# Test without auth (should return 401)
curl -X POST https://your-domain/api/gateway/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test with auth (should work)
curl -X POST https://your-domain/api/gateway/v1/chat/completions \
  -H "Authorization: Bearer $GATEWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🛠️ MCP Server Tools

### HuggingFace Gateway

**Available Tools:**

1. **`hf_list_models`** - Search models
   ```json
   {
     "search": "bert",
     "limit": 10
   }
   ```

2. **`hf_model_info`** - Get model details
   ```json
   {
     "model": "gpt2"
   }
   ```

3. **`hf_list_datasets`** - Search datasets
   ```json
   {
     "search": "squad",
     "limit": 5
   }
   ```

4. **`hf_list_spaces`** - Search Spaces
   ```json
   {
     "search": "text generation",
     "limit": 10
   }
   ```

5. **`hf_run_inference`** - Run inference
   ```json
   {
     "model": "gpt2",
     "inputs": "Once upon a time",
     "parameters": {
       "max_length": 50,
       "temperature": 0.8
     }
   }
   ```

### SocialPilot Gateway

**Available Tools:**

1. **`sp_list_accounts`** - List connected accounts
2. **`sp_create_post`** - Schedule post
   ```json
   {
     "message": "Hello world!",
     "accounts": "twitter_123,linkedin_456",
     "scheduledTime": "2024-01-15T10:00:00Z"
   }
   ```

3. **`sp_get_analytics`** - Get analytics
   ```json
   {
     "account": "twitter_123",
     "startDate": "2024-01-01",
     "endDate": "2024-01-31"
   }
   ```

4. **`sp_list_queues`** - List queued posts
5. **`sp_delete_post`** - Delete scheduled post

### Unito Gateway

**Available Tools:**

1. **`unito_list_workspaces`** - List workspaces
2. **`unito_list_integrations`** - List 60+ connectors
3. **`unito_list_syncs`** - List syncs
   ```json
   {
     "workspaceId": "ws_123"
   }
   ```

4. **`unito_create_sync`** - Create two-way sync
   ```json
   {
     "workspaceId": "ws_123",
     "name": "Jira to Asana Sync",
     "sourceConnector": "jira",
     "targetConnector": "asana"
   }
   ```

5. **`unito_get_sync`** - Get sync details
6. **`unito_update_sync`** - Pause/resume/archive

### WordPress.com Gateway

**Available Tools:**

1. **`wpcom_list_sites`** - List all sites
2. **`wpcom_create_post`** - Create post
   ```json
   {
     "site": "myblog.wordpress.com",
     "title": "My New Post",
     "content": "<p>Post content here</p>",
     "status": "publish",
     "tags": ["tech", "ai"]
   }
   ```

3. **`wpcom_list_posts`** - List posts
4. **`wpcom_get_post`** - Get single post
5. **`wpcom_update_post`** - Update post
6. **`wpcom_delete_post`** - Delete post

---

## 🔍 Debugging & Monitoring

### Check Gateway Status

```bash
# Test each gateway individually
node -e "
  console.log('Testing gateways...');
  // Add test code here
"
```

### View Logs

```bash
# MCP server logs go to stderr
node huggingface-gateway.js 2>hf.log

# View logs
tail -f hf.log
```

### Common Issues

#### 1. "Missing GATEWAY_KEY" Error

**Solution:** Set environment variables
```bash
export GATEWAY_KEY="your-key-here"
export HF_API_TOKEN="hf_xxxxx"
```

#### 2. Gateway 401/403 Errors

**Solution:** Check authentication
```bash
# Verify token is valid
curl -H "Authorization: Bearer $GATEWAY_KEY" \
  https://your-domain/api/gateway/v1/chat/completions
```

#### 3. Connection Timeout

**Solution:** Increase timeout or check network
```javascript
// In gateway file, adjust timeout:
signal: AbortSignal.timeout(60000) // 60 seconds
```

#### 4. Module Not Found

**Solution:** Reinstall dependencies
```bash
rm -rf node_modules package-lock.json
npm install
```

---

## 🧪 Testing Script

Create `test-gateways.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Testing MCP Gateways"
echo ""

# Load environment
source .env

# Test HuggingFace
echo "1️⃣ Testing HuggingFace Gateway..."
curl -X POST "$GATEWAY_URL/mcp/huggingface/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hf-mcp",
    "messages": [{"role":"user","content":"hf_list_models {\"search\":\"gpt2\"}"}]
  }' | jq .

echo ""

# Test SocialPilot
echo "2️⃣ Testing SocialPilot Gateway..."
curl -X POST "$GATEWAY_URL/mcp/socialpilot/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "socialpilot-mcp",
    "messages": [{"role":"user","content":"sp_list_accounts {}"}]
  }' | jq .

echo ""

# Test Unito
echo "3️⃣ Testing Unito Gateway..."
curl -X POST "$GATEWAY_URL/mcp/unito/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "unito-mcp",
    "messages": [{"role":"user","content":"unito_list_workspaces {}"}]
  }' | jq .

echo ""

# Test WordPress.com
echo "4️⃣ Testing WordPress.com Gateway..."
curl -X POST "$GATEWAY_URL/mcp/wpcom/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "wpcom-mcp",
    "messages": [{"role":"user","content":"wpcom_list_sites {}"}]
  }' | jq .

echo ""
echo "✅ All tests complete!"
```

**Run tests:**
```bash
chmod +x test-gateways.sh
./test-gateways.sh
```

---

## 📊 Production Deployment

### 1. Add to package.json

```json
{
  "scripts": {
    "mcp:hf": "node mcp-server/huggingface-gateway.js",
    "mcp:sp": "node mcp-server/socialpilot-gateway.js",
    "mcp:unito": "node mcp-server/unito-gateway.js",
    "mcp:wpcom": "node mcp-server/wpcom-gateway.js",
    "mcp:all": "concurrently \"npm:mcp:*\""
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "concurrently": "^8.0.0"
  }
}
```

### 2. Process Manager (PM2)

Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'mcp-huggingface',
      script: './mcp-server/huggingface-gateway.js',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'mcp-socialpilot',
      script: './mcp-server/socialpilot-gateway.js',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'mcp-unito',
      script: './mcp-server/unito-gateway.js',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'mcp-wpcom',
      script: './mcp-server/wpcom-gateway.js',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
```

**Deploy with PM2:**
```bash
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 3. Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --production

# Copy source
COPY mcp-server/ ./mcp-server/
COPY .env ./

# Expose ports if needed
EXPOSE 3000

# Run all gateways
CMD ["npm", "run", "mcp:all"]
```

**Build and run:**
```bash
docker build -t mcp-gateways .
docker run -d --env-file .env mcp-gateways
```

---

## 🔐 Security Best Practices

1. **Never commit secrets**
   ```bash
   # Add to .gitignore
   .env
   .env.*
   *.log
   ```

2. **Rotate tokens regularly**
   ```bash
   # Generate new API keys every 90 days
   ```

3. **Use different keys per environment**
   ```bash
   # .env.development
   GATEWAY_KEY=dev_key_xxx

   # .env.production
   GATEWAY_KEY=prod_key_xxx
   ```

4. **Enable rate limiting** (in gateway endpoint)
   ```javascript
   // Add to completions.js
   const rateLimit = new Map();
   // Implement rate limiting logic
   ```

---

## 📚 Additional Resources

- [MCP SDK Documentation](https://modelcontextprotocol.io)
- [HuggingFace API Docs](https://huggingface.co/docs/api-inference)
- [SocialPilot API](https://socialpilot.co/developers)
- [Unito API](https://guide.unito.io/api-documentation)
- [WordPress.com REST API](https://developer.wordpress.com/docs/api/)

---

## 🆘 Support

**If you encounter issues:**

1. Check environment variables are set
2. Verify API tokens are valid
3. Test gateway endpoint separately
4. Review error logs
5. Check network connectivity

**Need help?** Open an issue in the repository with:
- Error message
- Environment (dev/prod)
- Steps to reproduce
- Gateway logs
