# 🚀 Quick Start Guide

## Get Running in 5 Minutes

### Step 1: Clone & Setup
```bash
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-
```

### Step 2: Configure Environment
```bash
cp config/.env.example .env
# Edit .env and add your API keys
```

### Step 3: Deploy
```bash
chmod +x scripts/deploy-everything.sh
./scripts/deploy-everything.sh
```

### Step 4: Run Tax Agent
```bash
python3 src/agents/tax-collector-humanitarian.py
```

### Step 5: Monitor Results
```bash
# View detections
cat tax_agent_detections.json

# Check revenue
cat revenue_attribution.json

# View logs
tail -f logs/tax-agent.log
```

## What Happens When You Run

1. **Tax Agent scans GDELT** for hardship events (last 24h)
2. **3 Judges evaluate** each story (Mistral models)
3. **Content generated** if 2/3 judges approve
4. **Revenue tracked** from all sources
5. **Intervention triggered** when $5K threshold reached
6. **Victim contacted** and assistance provided

## Expected Results (First Run)

- **Stories Detected**: 3-5
- **Content Generated**: 2-3 blog posts + videos
- **Revenue**: $200-500 (simulated for testing)
- **Commission**: 15% automatically calculated

## Automation (After Setup)

Add to crontab for automatic execution:
```bash
# Run every 6 hours
0 */6 * * * cd /path/to/repo && python3 src/agents/tax-collector-humanitarian.py
```

## Monitoring Dashboard

Import `src/monitoring/grafana-dashboard.json` to:
https://dimakatsomoleli.grafana.net

Track:
- Stories detected
- Revenue generated
- Interventions funded
- Content performance

## Troubleshooting

**No stories detected?**
- GDELT might have no matching events in last 24h
- Try adjusting keywords in tax-collector-humanitarian.py

**Revenue not tracking?**
- Check .env has all API keys
- Verify revenue_attribution.json is writable

**Judges rejecting everything?**
- This is simulated for testing
- Real integration requires Mistral API calls

## Next Steps

1. Connect actual AI models (not simulated)
2. Integrate real payment processing
3. Add victim contact automation
4. Scale content distribution
5. Monitor revenue growth

**Go to sleep. Wake up to revenue and impact.** 🚀
