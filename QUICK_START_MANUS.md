# 🚀 QUICK START - Manus AI

## 📄 File to Use

**Main Instructions:** `manus-instructions.md` (553 lines)

This file contains everything Manus AI needs to:
1. Install Windsurf on Debian/Ubuntu
2. Configure 3 MCP servers
3. Execute 28-platform pipeline
4. Report results

---

## ⚡ 30-Second Summary for Manus

```plaintext
OBJECTIVE: Deploy and test 28-platform content distribution pipeline

STEPS:
1. Install Windsurf (2-3 min)
2. Configure MCP servers (30 sec)
3. OAuth authentication (2 min)
4. Run live test (60 sec)
5. Extract results (30 sec)
6. Generate report (30 sec)

TOTAL TIME: ~6-7 minutes

OUTPUT: Full metrics report showing:
- WordPress post URL
- 28 platform distribution results
- GitHub commit verification
- Email campaign status
- Run ID for Inngest dashboard
```

---

## 📋 What Manus Needs

### Required Information
- GitHub Personal Access Token (classic, with `repo` scope)
- RankYak webhook secret
- WordPress.com account credentials (for OAuth)

### System Requirements
- Debian/Ubuntu machine
- Node.js 18+
- Docker installed
- Internet connection

---

## 🎯 Expected Output

After execution, Manus should report:

```
✅ Live pipeline completed successfully
WordPress URL: https://[site].wordpress.com/manus-ai-live-demo-full-stack
GitHub commit: [Latest commit message]
Inngest dashboard: https://app.inngest.com/function/rankyak-publish/runs/[RUN_ID]
Email campaigns sent: [COUNT]
Total platforms: 28
Pipeline time: ~30 seconds
✅ All systems operational
```

---

## 📁 File Structure for Manus

```
manus-instructions.md          ← PASTE THIS INTO MANUS
├── Phase 1: Install Windsurf
├── Phase 2: Initialize config
├── Phase 3: Install dependencies
├── Phase 4: Deploy MCP config
├── Phase 5: Restart Windsurf
├── Phase 6: OAuth authentication
├── Phase 7: Execute pipeline
├── Phase 8: Extract results
├── Phase 9: Generate report
└── Phase 10: Clean-up (optional)
```

---

## 🔐 Security Notes

- All secrets are prompted securely via MCP input prompts
- No hardcoded credentials in config files
- HMAC-SHA256 signature verification on all webhooks
- OAuth flows handled by official MCP servers

---

## ✅ Success Indicators

Manus knows it's working when:

1. ✅ Windsurf starts without errors
2. ✅ All 3 MCP servers show "Connected"
3. ✅ WordPress post created (gets permalink)
4. ✅ Inngest returns Run ID
5. ✅ 28 platforms show success status
6. ✅ GitHub commit verified

---

## 🚨 If Something Fails

Manus should:
1. Check `/tmp/windsurf.log` for errors
2. Verify prerequisites are installed
3. Confirm Vercel deployment is live:
   ```bash
   curl https://snout-lard-jumbo-5158.vercel.app/api/inngest
   ```
4. Test MCP servers individually before combining

---

## 📞 Troubleshooting Commands

```bash
# Check Windsurf is running
pgrep -f windsurf

# View logs
tail -f /tmp/windsurf.log

# Test Vercel endpoint
curl -X POST https://snout-lard-jumbo-5158.vercel.app/api/inngest \
  -H "Content-Type: application/json" \
  -d '{"event":"test","data":{"title":"Test"}}'

# Verify Docker
docker ps
docker images | grep github-mcp-server

# Check npm global packages
npm list -g --depth=0 | grep http-mcp-server
```

---

## 🎊 Final Checklist for Manus

Before starting, verify:
- [ ] Have GitHub PAT ready
- [ ] Have RankYak webhook secret ready
- [ ] Machine is Debian/Ubuntu
- [ ] Node.js 18+ installed
- [ ] Docker is running
- [ ] Internet connection is stable

After completion, verify:
- [ ] WordPress post exists and is published
- [ ] Inngest dashboard shows completed run
- [ ] 28 platforms show in results
- [ ] GitHub shows latest commit
- [ ] No errors in logs

---

## 🎯 The One Command to Rule Them All

If Manus wants to paste everything at once:

```bash
# This will be in Phase 7 of manus-instructions.md
# Just copy the entire Phase 7 section into Windsurf chat
```

---

## 💡 Pro Tips for Manus

1. **Run phases sequentially** - don't skip ahead
2. **Wait for confirmations** - each step outputs a ✅
3. **Save the Run ID** - needed for tracking
4. **Copy full output** - needed for final report
5. **Test individually first** - verify each MCP works alone

---

## 📊 What This Proves

Successful completion demonstrates:

✅ Windsurf installation and configuration  
✅ Multi-MCP server orchestration  
✅ OAuth authentication flows  
✅ Real-time API integration  
✅ 28-platform parallel distribution  
✅ Webhook signature verification  
✅ GitHub commit automation  
✅ WordPress content management  
✅ Email campaign integration  
✅ End-to-end pipeline execution

---

## 🚀 Ready to Go!

**NEXT ACTION:** Paste entire contents of `manus-instructions.md` into Manus AI

---

*Generated: 2025-11-11*
*Domain: snout-lard-jumbo-5158.vercel.app*
*Status: ✅ PRODUCTION READY*
