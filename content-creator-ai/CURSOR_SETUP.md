# Running Content Creator AI in Cursor 🚀

## Quick Start in Cursor

### Step 1: Open Terminal in Cursor

Press `` Ctrl+` `` (or `Cmd+``) to open the integrated terminal.

### Step 2: Navigate to Project

```bash
cd /workspace/content-creator-ai
```

### Step 3: Install Dependencies

```bash
npm install
```

### Step 4: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Open .env in Cursor to edit
```

Add at least one API key to `.env`:
```env
# Choose your provider:
GOOGLE_API_KEY=your-google-api-key
# or
OPENAI_API_KEY=your-openai-key
# or
ZAI_API_KEY=your-zai-key

# Set your API key for the webhook
API_KEY=my-secure-api-key-123

# Choose default provider
DEFAULT_PROVIDER=google
```

### Step 5: Start the Server

```bash
npm start
```

You should see:
```
🚀 Content Creator AI Server Started
Server running on: http://localhost:3000
```

### Step 6: Open in Browser

Click the link in the terminal or manually open:
- **Web UI**: http://localhost:3000
- **Health Check**: http://localhost:3000/api/health
- **Test Endpoint**: http://localhost:3000/api/test

## Development Mode (Auto-Reload)

For development with auto-reload on file changes:

```bash
npm run dev
```

This uses `nodemon` to restart the server when you edit files.

## Testing in Cursor

### Option 1: Use the Browser UI
1. Open http://localhost:3000
2. Fill in the form
3. Click "Generate Content"

### Option 2: Use Cursor's Terminal

Test the API with curl:
```bash
# Test endpoint (no API key needed)
curl http://localhost:3000/api/test

# Health check
curl http://localhost:3000/api/health

# Real content generation
curl -X POST http://localhost:3000/api/content \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secure-api-key-123" \
  -d '{
    "topic": "Hello from Cursor!",
    "media_type": "text",
    "length": "short"
  }'
```

### Option 3: Run the Test Suite

```bash
node test.js
```

## Optional: LocalAI Setup in Cursor

If you want to test with LocalAI locally:

### Using Docker (Recommended)

```bash
# Start LocalAI in a separate terminal tab
docker run -p 8080:8080 --name localai localai/localai:latest-aio-cpu

# In .env, enable LocalAI:
LOCALAI_ENABLED=true
LOCALAI_URL=http://localhost:8080
```

### Using LocalAI Binary

```bash
# Install LocalAI
curl https://localai.io/install.sh | sh

# Run with a model
local-ai run llama-3.2-1b-instruct
```

Then update `.env`:
```env
LOCALAI_ENABLED=true
LOCALAI_URL=http://localhost:8080
```

## Optional: Redis Setup in Cursor

For caching support:

### Using Docker

```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

Update `.env`:
```env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
```

### Using Local Redis (if installed)

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

## Debugging in Cursor

### View Logs

```bash
# Real-time logs
tail -f logs/combined.log

# Error logs only
tail -f logs/error.log
```

### Check Server Status

```bash
# Health check
curl http://localhost:3000/api/health

# Stats
curl -H "X-API-Key: my-secure-api-key-123" http://localhost:3000/api/stats
```

### Stop the Server

In the terminal where the server is running:
- Press `Ctrl+C`

Or kill the process:
```bash
# Find the process
lsof -i :3000

# Kill it
kill -9 <PID>
```

## Common Issues in Cursor

### Port Already in Use

```bash
# Find what's using port 3000
lsof -i :3000

# Kill it
kill -9 <PID>

# Or use a different port
PORT=8080 npm start
```

### Module Not Found

```bash
# Reinstall dependencies
rm -rf node_modules
npm install
```

### Permission Errors

```bash
# Fix permissions
sudo chown -R $USER:$USER /workspace/content-creator-ai
```

## Deploying from Cursor

While you develop in Cursor, you can deploy to various platforms:

### 1. Deploy to Replit

1. Push your code to GitHub from Cursor
2. Import to Replit from GitHub
3. Add environment variables in Replit Secrets
4. Click Run

### 2. Deploy to Heroku

```bash
# In Cursor's terminal
heroku login
heroku create my-content-creator
heroku config:set GOOGLE_API_KEY=your-key
git push heroku main
```

### 3. Deploy with Docker

```bash
# Build
docker build -t content-creator-ai .

# Run
docker run -p 3000:3000 \
  -e GOOGLE_API_KEY=your-key \
  -e API_KEY=your-api-key \
  content-creator-ai
```

### 4. Deploy to VPS

```bash
# Push to GitHub from Cursor
git add .
git commit -m "Ready for deployment"
git push origin main

# Then SSH to your VPS and pull
ssh user@your-vps
git clone your-repo
cd content-creator-ai
npm install --production
pm2 start server.js
```

## Cursor-Specific Tips

### 1. Use Cursor's AI Features

Ask Cursor AI to:
- Explain any code in the project
- Help debug issues
- Suggest improvements
- Generate API request examples

### 2. Multi-Terminal Workflow

Open multiple terminals in Cursor:
- Terminal 1: Run the server (`npm start`)
- Terminal 2: Run tests (`node test.js`)
- Terminal 3: Test API calls with curl
- Terminal 4: Monitor logs (`tail -f logs/combined.log`)

### 3. Quick Commands

Add to your Cursor command palette:
- "Run Server": `npm start`
- "Run Tests": `node test.js`
- "View Logs": `tail -f logs/combined.log`

### 4. File Watching

Cursor will auto-detect file changes. The server will auto-reload if you use:
```bash
npm run dev
```

## Project Structure in Cursor

Open these files to understand the app:

```
📁 content-creator-ai/
├── 📄 server.js              ← Start here (main entry point)
├── 📁 config/
│   └── config.js             ← Configuration
├── 📁 controllers/
│   └── content.js            ← Request handlers
├── 📁 services/
│   └── providers/            ← AI provider integrations
├── 📁 routes/
│   └── api.js                ← API routes
├── 📁 public/
│   ├── css/style.css         ← Frontend styles
│   └── js/app.js             ← Frontend JavaScript
└── 📁 views/
    └── index.ejs             ← UI template
```

## Next Steps

1. ✅ Install dependencies: `npm install`
2. ✅ Configure `.env` with your API keys
3. ✅ Start the server: `npm start`
4. ✅ Open http://localhost:3000
5. ✅ Test the API
6. ✅ Deploy when ready

---

**Happy coding in Cursor! 🎯**
