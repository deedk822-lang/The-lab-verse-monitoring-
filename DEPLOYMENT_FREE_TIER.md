# 🆓 FREE Deployment Guide - Vercel + Render

**Total Cost: $0/month** 💰

## Architecture

```
┌─────────────────────────────────────────┐
│   FRONTEND (Next.js)                    │
│   Platform: Vercel                      │
│   Cost: FREE ✅                         │
│   Auto-deploys from GitHub              │
└──────────────┬──────────────────────────┘
               │ API calls
               ↓
┌─────────────────────────────────────────┐
│   BACKEND (FastAPI Python)              │
│   Platform: Render                      │
│   Cost: FREE ✅                         │
│   750 hours/month (enough for 24/7)    │
│   Auto-sleeps after 15 min idle        │
└─────────────────────────────────────────┘
```

---

## Step 1: Deploy Backend to Render (5 minutes)

### 1.1 Sign Up
- Go to [render.com](https://render.com)
- Click **"Get Started"**
- Sign in with GitHub (easiest)

### 1.2 Create New Web Service
- Click **"New +"** → **"Web Service"**
- Click **"Build and deploy from a Git repository"**
- Click **"Connect account"** (if first time)
- Find and select: `deedk822-lang/The-lab-verse-monitoring-`
- Click **"Connect"**

### 1.3 Configure Service

**Branch:** `feature/complete-orchestrator-and-scheduler`

**Root Directory:** `rainmaker_orchestrator`

**Runtime:** `Python 3`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

**Instance Type:** `Free` ✅

### 1.4 Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**:

```
KIMI_API_KEY = your_actual_kimi_api_key_here
KIMI_API_BASE = https://api.moonshot.ai/v1
LOG_LEVEL = INFO
WORKSPACE_PATH = /opt/render/project/src/workspace
ENVIRONMENT = production
```

### 1.5 Deploy!
- Click **"Create Web Service"**
- Wait 3-5 minutes for first build
- Your backend URL: `https://rainmaker-orchestrator.onrender.com`

---

## Step 2: Deploy Frontend to Vercel (3 minutes)

### 2.1 Sign Up
- Go to [vercel.com](https://vercel.com)
- Click **"Start Deploying"**
- Sign in with GitHub

### 2.2 Import Project
- Click **"Add New..."** → **"Project"**
- Find: `deedk822-lang/The-lab-verse-monitoring-`
- Click **"Import"**

### 2.3 Configure Project

**Framework Preset:** `Next.js` (auto-detected)

**Branch:** `feature/complete-orchestrator-and-scheduler`

**Root Directory:** `./` (leave as default)

**Environment Variables:** (Already in `vercel.json` ✅)

### 2.4 Deploy!
- Click **"Deploy"**
- Wait 2-3 minutes
- Your frontend URL: `https://the-lab-verse-monitoring.vercel.app`

---

## Step 3: Test Everything

### Test Backend
```bash
curl https://rainmaker-orchestrator.onrender.com/health
```

**Expected Response:**
```json
{"status": "healthy", "timestamp": "..."}
```

### Test Frontend
Visit: `https://the-lab-verse-monitoring.vercel.app`

### Test Integration
Your Next.js app will automatically call the Render backend!

---

## FREE Tier Limits (You're Safe! ✅)

### Vercel FREE:
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Git integration

### Render FREE:
- ✅ 750 hours/month (31 days = 744 hours - perfect!)
- ✅ 512 MB RAM
- ✅ Automatic HTTPS
- ✅ Custom domains
- ⚠️ Sleeps after 15 min inactivity (wakes in ~30 seconds)

---

## Important Notes

### Backend Sleep Mode
Render's free tier **sleeps after 15 minutes** of inactivity. First request after sleep takes ~30 seconds.

**Solutions:**
1. **Accept it** - Most personal projects are fine with this
2. **Keep-alive ping** - Add this to your frontend (optional):

```typescript
// In your Next.js app
setInterval(() => {
  fetch('https://rainmaker-orchestrator.onrender.com/health')
}, 14 * 60 * 1000) // Ping every 14 minutes
```

### Update Backend URL
If your Render URL is different, update `vercel.json`:

```json
"env": {
  "NEXT_PUBLIC_API_ENDPOINT": "https://YOUR-ACTUAL-URL.onrender.com"
}
```

Then commit and push - Vercel will auto-redeploy.

---

## Monitoring & Logs

### Render Dashboard
- View logs: [dashboard.render.com](https://dashboard.render.com)
- Monitor uptime, requests, errors

### Vercel Dashboard
- View deployments: [vercel.com/dashboard](https://vercel.com/dashboard)
- Analytics, performance metrics

---

## Troubleshooting

### Backend won't start?
1. Check logs in Render dashboard
2. Verify all environment variables are set
3. Check `requirements.txt` has all dependencies

### Frontend can't reach backend?
1. Verify backend is running: `curl https://rainmaker-orchestrator.onrender.com/health`
2. Check CORS settings in `server.py`
3. Inspect browser console for errors

### Need help?
Check the logs in both Render and Vercel dashboards!

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Vercel
3. ✅ Test everything
4. 🎉 You're live on 100% FREE hosting!

**Total time:** ~10 minutes
**Total cost:** $0/month
**Maintenance:** Auto-deploys from GitHub

---

## Optional: Custom Domain

Both platforms support FREE custom domains:

### Vercel:
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records

### Render:
1. Go to Service Settings → Custom Domain
2. Add your domain
3. Update DNS records

---

**Questions?** The config files are ready - just follow the steps above! 🚀
