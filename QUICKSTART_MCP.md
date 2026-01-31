# The Lab-Verse MCP Integration - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get your MCP-integrated workflow automation system up and running quickly.

---

## Prerequisites

✅ Node.js 18+ installed  
✅ Git installed  
✅ `manus-mcp-cli` available  
✅ MCP servers authenticated (Asana, Notion, Airtable, Gmail, Hugging Face)

---

## Step 1: Clone & Install (1 minute)

```bash
# Already cloned? Skip to Step 2
cd ~/The-lab-verse-monitoring-

# Install dependencies (if not done)
npm install
```

---

## Step 2: Configure Environment (2 minutes)

```bash
# Copy environment template
cp .env.mcp .env.mcp.local

# Get your Asana workspace ID
manus-mcp-cli tool call asana_list_workspaces --server asana --input '{}'

# Get your Airtable base ID
manus-mcp-cli tool call list_bases --server airtable --input '{}'

# Edit .env.mcp.local with your IDs
nano .env.mcp.local
```

**Minimum required configuration**:
```bash
ASANA_WORKSPACE_ID=your_workspace_gid_here
NOTION_WORKSPACE_ID=your_workspace_id_here
AIRTABLE_BASE_METRICS=your_base_id_here
GMAIL_SENDER_EMAIL=deedk822@gmail.com
```

---

## Step 3: Run Setup Wizard (2 minutes)

```bash
./launch-mcp-system.sh
```

Select **Option 3: Setup Wizard**

The wizard will:
- ✅ Create Asana projects
- ✅ Verify Notion connection
- ✅ Configure Airtable
- ✅ Test Gmail
- ✅ Save configuration

---

## Step 4: Verify & Launch (1 minute)

```bash
# Verify setup
./launch-mcp-system.sh
# Select Option 4: Run System Verification

# Launch system
./launch-mcp-system.sh
# Select Option 1: Launch Full System
```

---

## 🎯 Test Your First Workflow

### Test SEO Ranking Drop Response

```bash
./launch-mcp-system.sh
# Select Option 2: Test Individual Workflow
# Select 1: SEO Ranking Drop Response
```

**What happens**:
1. ✅ Creates record in Airtable
2. ✅ Creates urgent task in Asana
3. ✅ Updates Notion dashboard
4. ✅ Sends email alert

**Check results**:
- Go to your Asana workspace → "Lab-Verse: SEO Recovery" project
- Check your email for alert
- View Notion dashboard for metrics

---

## 📊 Available Workflows

### 1. SEO Ranking Drop Response
**Trigger**: Ranking drops > 5 positions  
**Use**: `orchestrator.handleSEORankingDrop(keyword, prevPos, currPos, url)`

### 2. High-Performing Content Amplification
**Trigger**: Email CTR > 15%  
**Use**: `orchestrator.amplifyHighPerformingContent(title, url, ctr, clicks)`

### 3. Crisis Event Response
**Trigger**: GDELT urgency > 75  
**Use**: `orchestrator.handleCrisisEvent(description, urgency, regions)`

### 4. B2B Client Onboarding
**Trigger**: PayPal payment received  
**Use**: `orchestrator.onboardB2BClient(email, name, product, amount, txnId)`

### 5. Weekly Performance Report
**Trigger**: Scheduled (Monday 9 AM)  
**Use**: `orchestrator.generateWeeklyReport()`

---

## 🔧 Programmatic Usage

```javascript
const MCPOrchestrator = require('./src/mcp-orchestrator.js');

const orchestrator = new MCPOrchestrator();

// Initialize
await orchestrator.initialize();

// Example: Handle SEO ranking drop
await orchestrator.handleSEORankingDrop(
  'african trade policy',
  3,  // was position 3
  8,  // now position 8
  'https://deedk822.wordpress.com/article'
);

// Example: Amplify high-performing content
await orchestrator.amplifyHighPerformingContent(
  'Breaking Trade News',
  'https://deedk822.wordpress.com/news',
  0.18,  // 18% CTR
  250    // 250 clicks
);

// Example: Generate weekly report
await orchestrator.generateWeeklyReport();
```

---

## 📁 MCP Integration Files

```
The-lab-verse-monitoring-/
├── src/
│   └── mcp-orchestrator.js       # Main orchestration engine
├── scripts/
│   └── setup-wizard.js           # Interactive setup
├── launch-mcp-system.sh          # System launcher
├── .env.mcp                      # Environment template
├── MCP_INTEGRATION_README.md    # Full documentation
├── MCP_INTEGRATION_PLAN.md      # Technical plan
├── DEPLOYMENT_GUIDE_MCP.md      # Deployment guide
└── QUICKSTART_MCP.md            # This file
```

---

## 🔍 Verify MCP Servers

```bash
# Test all MCP servers
manus-mcp-cli tool list --server asana
manus-mcp-cli tool list --server notion
manus-mcp-cli tool list --server airtable
manus-mcp-cli tool list --server gmail
manus-mcp-cli tool list --server hugging-face
```

All should return a list of available tools. If not, authenticate the server.

---

## 🐛 Troubleshooting

### Issue: "MCP server timeout"
**Solution**: Increase timeout in `src/mcp-orchestrator.js` line 20

### Issue: "Missing environment variables"
**Solution**: Verify `.env.mcp` is loaded: `source .env.mcp`

### Issue: "Authentication error"
**Solution**: Re-authenticate MCP server and restart

### Issue: "Tool not found"
**Solution**: Check tool name spelling and server name

---

## 📚 Next Steps

1. **Read Full Documentation**: `MCP_INTEGRATION_README.md`
2. **Review Deployment Guide**: `DEPLOYMENT_GUIDE_MCP.md`
3. **Customize Workflows**: Edit `src/mcp-orchestrator.js`
4. **Add More Workflows**: Follow existing patterns
5. **Monitor Performance**: Check logs and metrics

---

## 🎉 You're Ready!

Your workflow automation system is now running. The system will:

✅ Monitor SEO rankings  
✅ Amplify high-performing content  
✅ Respond to crisis events  
✅ Onboard B2B clients  
✅ Generate weekly reports  

All automatically, 24/7!

---

## 📞 Support

- **Documentation**: `MCP_INTEGRATION_README.md`
- **Issues**: Check logs in `/tmp/launch-*.log`
- **Contact**: deedk822@gmail.com

---

**Last Updated**: November 28, 2025  
**Version**: 1.0.0  
**Status**: 🚀 Production Ready
