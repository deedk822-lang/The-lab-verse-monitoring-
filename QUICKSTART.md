# Quick Start Guide - The Lab Verse Monitoring

## 🚀 Get Started in 3 Commands

### Prerequisites
- Node.js 18+ installed
- Redis server running (for BullMQ)

### Step 1: Install Dependencies
```bash
cd lapverse-core
npm install
```

### Step 2: Verify Configuration
```bash
# Check that .env.local exists with your API keys
cat ../.env.local

# Should show:
# DASHSCOPE_API_KEY=sk-d2362e0f03344f3bbd05d7df5efa7180
# MOONSHOT_API_KEY=key_ff71fc1b3b3401d7b52cbeb0534128b61609ebd104946e21a870c000394ab2bb
# ARTIFACT_TRACE_ENABLED=true
```

### Step 3: Start the Server
```bash
npm run dev
```

**Expected Output:**
```
♛ TheLapVerseCore live on port 3000
```

---

## 🧪 Test the AI Integration

### Test 1: Health Check with AI Analysis
```bash
curl http://localhost:3000/api/v2/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "metrics": { ... },
  "qwen_analysis": "...",
  "kimi_evolutions": [...]
}
```

### Test 2: Run the AI Connector Test Script
```bash
npx tsx test-ai-connector.ts
```

**Expected Output:**
```
Testing AI Connector...
DASHSCOPE_API_KEY: ✓ Set
MOONSHOT_API_KEY: ✓ Set

✓ CONNECTED - AI Response:
Qwen Analysis: ...
Kimi Response: ...

Test successful! Both AI engines are working.
```

---

## 📊 Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/health` | GET | AI-powered health analysis |
| `/api/v2/tasks` | POST | Submit task for processing |
| `/api/v2/self-compete` | POST | Start self-competition |
| `/api/v2/self-compete/:id` | GET | Get competition status |
| `/api/status` | GET | SLO and cost status |
| `/metrics` | GET | Prometheus metrics |

---

## 🔧 Configuration

### Environment Variables

Edit `.env.local` in the repository root:

```bash
# AI API Keys
DASHSCOPE_API_KEY=sk-your-alibaba-key
MOONSHOT_API_KEY=key_your-moonshot-key

# Optional
ARTIFACT_TRACE_ENABLED=true
REDIS_URL=redis://localhost:6379
PORT=3000
```

### Redis Setup (Required)

**Using Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**Using Homebrew (macOS):**
```bash
brew install redis
brew services start redis
```

**Using apt (Ubuntu):**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

---

## 🐛 Troubleshooting

### Issue: "Redis connection failed"
**Solution:** Start Redis server
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### Issue: "API key required"
**Solution:** Verify .env.local exists and contains valid keys
```bash
cat ../.env.local
```

### Issue: "Module not found"
**Solution:** Reinstall dependencies
```bash
npm install
```

---

## 📚 Next Steps

1. **Deploy to Production**: See `SETUP_VERIFICATION_REPORT.md` for deployment checklist
2. **Set up Monitoring**: Configure Prometheus + Grafana dashboards
3. **Enable Alerts**: Configure AlertManager rules
4. **Scale Workers**: Adjust BullMQ concurrency in `TheLapVerseCore.ts`

---

## 💡 Tips

- **Development Mode**: Use `npm run dev` for hot-reload
- **Production Build**: Run `npm run build && npm start`
- **Type Checking**: Run `npm run typecheck` before deployment
- **Logs**: Check console output for SecureLogger messages

---

**Ready to go!** 🎉

When you see successful AI responses, you've unlocked the full power of The Lab Verse Monitoring with dual-engine AI capabilities.
