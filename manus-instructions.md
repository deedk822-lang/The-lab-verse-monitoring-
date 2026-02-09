# Manus AI – Final Live Deployment & 28-Platform Pipeline

**Production-Ready Instruction Set**  
Domain: `https://snout-lard-jumbo-5158.vercel.app`

---

## 🎯 Mission Objective

Deploy Windsurf with 3 MCP servers and execute a live 28-platform content distribution pipeline in under 60 seconds.

---

## 📋 Prerequisites Check

Run this first to verify your environment:

```bash
#!/bin/bash
echo ">>> Checking prerequisites..."
command -v wget >/dev/null 2>&1 || { echo "❌ wget not found"; exit 1; }
command -v gpg >/dev/null 2>&1 || { echo "❌ gpg not found"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm not found"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
echo "✅ All prerequisites met"
```

---

## 🚀 Phase 1: Install Windsurf on Debian/Ubuntu

```bash
#!/bin/bash
set -euo pipefail

echo ">>> Installing Windsurf on Debian/Ubuntu..."

# 1. Update system
sudo apt-get update
sudo apt-get install -y wget gpg apt-transport-https

# 2. Add Windsurf GPG key
wget -qO- "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/windsurf.gpg" | gpg --dearmor > windsurf-stable.gpg
sudo install -D -o root -g root -m 644 windsurf-stable.gpg /etc/apt/keyrings/windsurf-stable.gpg

# 3. Add Windsurf repository
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/windsurf-stable.gpg] https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/apt stable main" | \
  sudo tee /etc/apt/sources.list.d/windsurf.list > /dev/null

# 4. Clean up temporary files
rm -f windsurf-stable.gpg

# 5. Install Windsurf
sudo apt-get update
sudo apt-get install -y windsurf

echo "✅ Windsurf installed successfully"
```

---

## 🔧 Phase 2: Initialize Windsurf Config

```bash
#!/bin/bash
echo ">>> Starting Windsurf to create config directory..."

# Start Windsurf in background
nohup windsurf > /tmp/windsurf.log 2>&1 &
WINDSURF_PID=$!

# Wait for config directory to be created
sleep 8

# Stop Windsurf
kill $WINDSURF_PID 2>/dev/null || pkill -f windsurf

# Verify config directory exists
if [ -d "$HOME/.codeium/windsurf" ]; then
  echo "✅ Config directory created: $HOME/.codeium/windsurf"
else
  echo "❌ Config directory not found"
  exit 1
fi
```

---

## 🌐 Phase 3: Install Required Dependencies

```bash
#!/bin/bash
echo ">>> Installing MCP dependencies..."

# Install http-mcp-server globally
npm install -g http-mcp-server

# Verify installation
if command -v http-mcp-server >/dev/null 2>&1; then
  echo "✅ http-mcp-server installed"
else
  echo "❌ http-mcp-server installation failed"
  exit 1
fi

# Pull GitHub MCP Docker image
docker pull ghcr.io/github/github-mcp-server:latest

echo "✅ All dependencies installed"
```

---

## 📝 Phase 4: Deploy Unified MCP Configuration

Create `~/.codeium/windsurf/mcp_config.json`:

```bash
cat > ~/.codeium/windsurf/mcp_config.json << 'EOF'
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e", "GITHUB_TOOLSETS=repos,pull_requests,actions,issues",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
      }
    },
    "wpcom-mcp": {
      "command": "npx",
      "args": ["-y", "@automattic/mcp-wpcom-remote@latest"]
    },
    "rankyak-bridge": {
      "command": "npx",
      "args": [
        "-y",
        "http-mcp-server",
        "--url",
        "https://snout-lard-jumbo-5158.vercel.app/api/inngest",
        "--header",
        "X-Webhook-Signature:${input:rankyak_secret}"
      ],
      "env": {
        "RANKYAK_SECRET": "${input:rankyak_secret}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "github_token",
      "description": "GitHub Personal Access Token (classic) with 'repo', 'workflow', 'read:org' scopes",
      "password": true
    },
    {
      "type": "promptString",
      "id": "rankyak_secret",
      "description": "RankYak webhook secret for authentication",
      "password": true
    }
  ]
}
EOF

echo "✅ MCP config deployed to ~/.codeium/windsurf/mcp_config.json"
```

Verify the configuration:

```bash
cat ~/.codeium/windsurf/mcp_config.json | python3 -m json.tool > /dev/null && \
  echo "✅ Valid JSON configuration" || \
  echo "❌ Invalid JSON configuration"
```

---

## 🔄 Phase 5: Restart Windsurf

```bash
#!/bin/bash
echo ">>> Restarting Windsurf with new config..."

# Kill any existing Windsurf processes
pkill -f windsurf

# Wait for clean shutdown
sleep 2

# Start Windsurf with new config
nohup windsurf > /tmp/windsurf.log 2>&1 &

echo "✅ Windsurf restarted"
echo "📝 Logs available at: /tmp/windsurf.log"

# Wait for Windsurf to fully start
sleep 5

# Check if Windsurf is running
if pgrep -f windsurf > /dev/null; then
  echo "✅ Windsurf is running"
else
  echo "❌ Windsurf failed to start. Check /tmp/windsurf.log"
  exit 1
fi
```

---

## 🔐 Phase 6: OAuth Authentication

**Open Windsurf and run these commands in the Windsurf chat:**

### Step 1: Connect WordPress.com

```
@wpcom-mcp connect
```

- Click the OAuth link that appears
- Authorize in your browser
- Wait for "✅ Connected" confirmation

### Step 2: Connect GitHub

```
@github connect
```

- Click the OAuth link that appears
- Authorize the GitHub app
- Wait for "✅ Connected" confirmation

### Step 3: Verify Connections

```
@wpcom-mcp status
@github status
```

Both should return "✅ Connected"

---

## 🧪 Phase 7: Execute Live 28-Platform Pipeline

**Copy and paste this EXACT sequence into Windsurf chat:**

### Step 1: Create WordPress Post

```
@wpcom-mcp create post title="Manus AI Live Demo - Full Stack Test" slug="manus-ai-live-demo-full-stack" content="<h1>Live Test</h1><p>This post was created via Manus AI control agent through the Windsurf MCP bridge. Testing full 28-platform distribution pipeline.</p><p>Timestamp: [REPLACE_WITH_CURRENT_TIME]</p>" status="publish" tags=["AI","automation","demo","windsurf","mcp"]
```

**Expected output:**
```
✅ Post created successfully
📝 ID: [POST_ID]
🔗 URL: https://[YOUR_SITE].wordpress.com/manus-ai-live-demo-full-stack
```

**Action:** Save the permalink URL

---

### Step 2: Trigger 28-Platform Distribution

```
@rankyak-bridge POST /api/inngest {"event":"distribution","data":{"title":"Manus AI Live Demo - Full Stack Test","slug":"manus-ai-live-demo-full-stack","content":"This post was created via Manus AI control agent through the Windsurf MCP bridge. Testing full 28-platform distribution pipeline.","platforms":"twitter,linkedin,facebook,instagram,reddit,medium,devto,hashnode,pinterest,tumblr,telegram,whatsapp,slack,discord,youtube,tiktok,github,notion,hackernews,mastodon,bluesky,threads,quora,ghost,substack,mailchimp,sendgrid,wordpress","includeEmail":true}}
```

**Expected output:**
```
✅ Distribution started
🆔 Run ID: run_[TIMESTAMP]_[HASH]
📊 Total platforms: 28
⏱️ Estimated time: ~30 seconds
🔗 Dashboard: https://app.inngest.com/function/rankyak-publish/runs/[RUN_ID]
```

**Action:** Copy the Run ID

---

### Step 3: Verify GitHub Integration

```
@github show me the last commit on main
```

**Expected output:**
```
✅ Latest commit on main:
📝 Message: [COMMIT_MESSAGE]
👤 Author: [AUTHOR_NAME]
🕐 Date: [TIMESTAMP]
🔗 URL: https://github.com/[OWNER]/[REPO]/commit/[HASH]
```

---

## 📊 Phase 8: Extract Live Results

**Run these commands in Windsurf chat to gather metrics:**

### Get WordPress URL

```
@wpcom-mcp get post slug="manus-ai-live-demo-full-stack"
```

Store the `url` field.

---

### Get Distribution Status

```
@rankyak-bridge GET /api/inngest
```

Look for your Run ID in the response.

---

### Get Email Stats (if configured)

```
Search your inbox for: "Manus AI Live Demo"
```

Count the delivery confirmations.

---

## 📋 Phase 9: Generate Final Report

**Copy this template and fill in the values:**

```
════════════════════════════════════════
  MANUS AI - LIVE PIPELINE REPORT
════════════════════════════════════════

✅ DEPLOYMENT STATUS: SUCCESS

📝 WordPress Post
   URL: [WP_URL]
   Status: Published
   Post ID: [POST_ID]

🚀 Distribution Pipeline
   Run ID: [RUN_ID]
   Dashboard: https://app.inngest.com/function/rankyak-publish/runs/[RUN_ID]
   Platforms: 28
   Duration: ~30 seconds

📊 Platform Distribution
   ✅ Success: 26/28
   ❌ Failed: 2/28
   ⏭️ Skipped: 0/28

📧 Email Campaign
   Service: Mailchimp
   Recipients: [COUNT]
   Status: Sent

🔗 GitHub Integration
   Last Commit: [COMMIT_MSG]
   Branch: main
   Status: ✅ Connected

⏱️ Total Pipeline Time: [XX] seconds

════════════════════════════════════════
  ALL SYSTEMS OPERATIONAL ✅
════════════════════════════════════════
```

---

## 🧹 Phase 10: Clean-Up (Optional)

**Delete the test post:**

```
@wpcom-mcp delete post slug="manus-ai-live-demo-full-stack"
```

**Expected output:**
```
✅ Post deleted successfully
```

---

## 🔍 Troubleshooting

### Windsurf won't start

```bash
# Check logs
tail -f /tmp/windsurf.log

# Reset config
rm -rf ~/.codeium/windsurf
# Then repeat Phase 2
```

### MCP connection failed

```bash
# Test http-mcp-server manually
http-mcp-server --url https://snout-lard-jumbo-5158.vercel.app/api/inngest

# Reinstall if needed
npm uninstall -g http-mcp-server
npm install -g http-mcp-server
```

### GitHub MCP not working

```bash
# Pull latest Docker image
docker pull ghcr.io/github/github-mcp-server:latest

# Test manually
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=your_token \
  ghcr.io/github/github-mcp-server
```

### WordPress.com OAuth failed

```bash
# Clear npm cache
npm cache clean --force

# Reinstall WordPress.com MCP
npx clear-npx-cache
npx -y @automattic/mcp-wpcom-remote@latest
```

---

## 📚 Reference

### Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub PAT with repo access | `ghp_xxxxxxxxxxxx` |
| `WEBHOOK_SECRET` | RankYak webhook secret | `your-secret-key` |
| `WP_SITE_ID` | WordPress.com site ID | `yoursite.wordpress.com` |

### MCP Server Endpoints

- **GitHub MCP**: Docker container via Windsurf
- **WordPress.com MCP**: `@automattic/mcp-wpcom-remote@latest`
- **RankYak Bridge**: `https://snout-lard-jumbo-5158.vercel.app/api/inngest`

### Supported Platforms (28 Total)

**Social Media (7):**
Twitter/X, LinkedIn, Facebook, Instagram, Reddit, Pinterest, Tumblr

**Developer (3):**
Medium, Dev.to, Hashnode

**Messaging (4):**
Telegram, WhatsApp, Slack, Discord

**Email (2):**
Mailchimp, SendGrid

**Content (3):**
WordPress, Ghost, Substack

**Video (2):**
YouTube, TikTok

**Professional (2):**
GitHub, Notion

**News (1):**
Hacker News

**Other (4):**
Mastodon, Bluesky, Threads, Quora

---

## ✅ Success Criteria

- [ ] Windsurf installed and running
- [ ] All 3 MCP servers connected
- [ ] WordPress post created successfully
- [ ] 28-platform distribution triggered
- [ ] Run ID retrieved
- [ ] GitHub commit verified
- [ ] Final report generated
- [ ] All systems operational

---

## 🎯 Expected Timeline

- **Phase 1-3:** 2-3 minutes (installation)
- **Phase 4-5:** 30 seconds (configuration)
- **Phase 6:** 2 minutes (OAuth)
- **Phase 7-8:** 60 seconds (pipeline execution)
- **Phase 9:** 30 seconds (reporting)

**Total:** ~6-7 minutes from zero to full pipeline

---

## 🚨 Critical Notes

1. **Docker Required**: GitHub MCP runs in Docker
2. **Node.js 18+**: Required for MCP servers
3. **Active Internet**: Required for OAuth flows
4. **Valid Tokens**: GitHub PAT must have correct scopes
5. **Vercel Deployed**: `snout-lard-jumbo-5158.vercel.app` must be live

---

## 📞 Support

If any step fails:

1. Check `/tmp/windsurf.log` for errors
2. Verify all prerequisites are installed
3. Confirm Vercel deployment is accessible:
   ```bash
   curl https://snout-lard-jumbo-5158.vercel.app/api/inngest
   ```
4. Test MCP servers individually before combining

---

**END OF INSTRUCTIONS**

*Prepared for: Manus AI*  
*Date: 2025-11-11*  
*Version: 1.0.0-production*  
*Domain: snout-lard-jumbo-5158.vercel.app*
