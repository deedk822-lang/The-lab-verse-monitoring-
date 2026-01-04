# Webhook Setup Guide - Lab-Verse Monitoring System

This guide shows you exactly how to configure webhooks in each platform to send real-time events to your Lab-Verse monitoring system.

---

## Prerequisites

1. Your Lab-Verse system is deployed and accessible at: `https://yourdomain.com`
2. All services are running and healthy
3. You have admin access to all platforms

---

## 1. Grafana Webhook Configuration

### Step 1: Access Grafana Alerting

1. Go to https://somoleli.grafana.net
2. Navigate to **Alerting** → **Contact points**
3. Click **New contact point**

### Step 2: Configure Webhook

```
Name: Lab-Verse Monitoring
Type: webhook

Webhook URL: https://yourdomain.com/webhooks/grafana
HTTP Method: POST

Optional: Add custom header
Header: X-Grafana-Token
Value: <your-grafana-webhook-token>
```

### Step 3: Test Connection

Click **Test** to send a test alert to Lab-Verse

### Step 4: Add to Alert Rules

1. Go to **Alert rules**
2. Edit existing rules or create new ones
3. In **Contact point**, select **Lab-Verse Monitoring**
4. Save

✅ Grafana webhooks are now configured!

---

## 2. HubSpot Webhook Configuration

### Step 1: Access HubSpot Settings

1. Go to https://app-eu1.hubspot.com
2. Click **Settings** (⚙️ icon)
3. Navigate to **Integrations** → **Private Apps**

### Step 2: Create Private App (if not exists)

1. Click **Create a private app**
2. Name: `Lab-Verse Integration`
3. Scopes needed:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
4. Click **Create app**
5. Copy the **Access Token** → Add to `.env` as `HUBSPOT_ACCESS_TOKEN`

### Step 3: Configure Webhooks

1. Go to **Settings** → **Integrations** → **Webhooks**
2. Click **Create subscription**

**Contact Created:**
```
URL: https://yourdomain.com/webhooks/hubspot
Subscription type: contact.creation
Format: JSON
```

**Contact Updated:**
```
URL: https://yourdomain.com/webhooks/hubspot
Subscription type: contact.propertyChange
Format: JSON
```

**Deal Created:**
```
URL: https://yourdomain.com/webhooks/hubspot
Subscription type: deal.creation
Format: JSON
```

**Deal Updated:**
```
URL: https://yourdomain.com/webhooks/hubspot
Subscription type: deal.propertyChange
Format: JSON
```

### Step 4: Get Webhook Secret

1. After creating subscriptions, HubSpot will provide a **Client Secret**
2. Copy it → Add to `.env` as `HUBSPOT_WEBHOOK_SECRET`

✅ HubSpot webhooks are now configured!

---

## 3. ClickUp Webhook Configuration

### Step 1: Get API Token

1. Go to https://app.clickup.com
2. Click your profile → **Settings**
3. Navigate to **Apps**
4. Generate new **API Token**
5. Copy token → Add to `.env` as `CLICKUP_API_TOKEN`

### Step 2: Get Workspace ID

1. Open your workspace
2. URL will be: `app.clickup.com/<WORKSPACE_ID>/`
3. Copy workspace ID → Add to `.env` as `CLICKUP_WORKSPACE_ID`

### Step 3: Configure Webhooks via API

Since ClickUp webhooks are set via API, use this script:

```bash
#!/bin/bash

CLICKUP_TOKEN="your-clickup-token"
WORKSPACE_ID="your-workspace-id"
WEBHOOK_URL="https://yourdomain.com/webhooks/clickup"

# Create webhook for task events
curl -X POST "https://api.clickup.com/api/v2/team/${WORKSPACE_ID}/webhook" \
  -H "Authorization: ${CLICKUP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "'${WEBHOOK_URL}'",
    "events": [
      "taskCreated",
      "taskUpdated",
      "taskDeleted",
      "taskStatusUpdated"
    ]
  }'
```

### Step 4: Verify Webhooks

```bash
# List all webhooks
curl -X GET "https://api.clickup.com/api/v2/team/${WORKSPACE_ID}/webhook" \
  -H "Authorization: ${CLICKUP_TOKEN}"
```

✅ ClickUp webhooks are now configured!

---

## 4. DataDog Webhook Configuration

### Step 1: Get API Keys

1. Go to https://app.datadoghq.eu
2. Navigate to **Organization Settings** → **API Keys**
3. Create new API Key → Copy → Add to `.env` as `DATADOG_API_KEY`
4. Go to **Application Keys**
5. Create new Application Key → Copy → Add to `.env` as `DATADOG_APP_KEY`

### Step 2: Configure Webhook Integration

1. Go to **Integrations** → **Webhooks**
2. Click **New**

```
Name: Lab-Verse Monitoring
URL: https://yourdomain.com/webhooks/datadog
Payload: Use default

Custom Headers (optional):
X-DataDog-Source: monitoring
```

### Step 3: Add to Monitors

1. Go to **Monitors** → **Manage Monitors**
2. Edit existing monitors or create new
3. In **Notify your team**, add:

```
@webhook-lab-verse-monitoring
```

✅ DataDog webhooks are now configured!

---

## 5. Confluence Webhook Configuration

Confluence webhooks require an app. Alternatively, use polling (already configured).

### Alternative: Use Polling

Lab-Verse automatically syncs Confluence data every hour. No webhook needed.

To trigger manual sync:

```bash
curl -X POST http://localhost/api/sync \
  -H "Content-Type: application/json" \
  -d '{"platforms": ["confluence"]}'
```

✅ Confluence integration configured via polling!

---

## 6. GitHub Webhooks (for CodeRabbit)

### Step 1: Access Repository Settings

1. Go to https://github.com/deedk822-lang/The-lab-verse-monitoring-
2. Click **Settings** → **Webhooks**
3. Click **Add webhook**

### Step 2: Configure Webhook

```
Payload URL: https://yourdomain.com/webhooks/github
Content type: application/json
Secret: <generate secure string, add to .env as GITHUB_WEBHOOK_SECRET>

Events to trigger:
☑ Pull requests
☑ Pull request reviews
☑ Push events
☑ Workflow runs
```

### Step 3: Activate

Click **Add webhook**

✅ GitHub webhooks configured!

---

## 7. Testing All Webhooks

### Test Script

Create `test_webhooks.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost"

echo "Testing Lab-Verse Webhooks..."

# Test Grafana webhook
echo -n "Grafana... "
curl -X POST "$BASE_URL/webhooks/grafana" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Alert","state":"alerting"}' \
  -s -o /dev/null -w "%{http_code}\n"

# Test HubSpot webhook
echo -n "HubSpot... "
curl -X POST "$BASE_URL/webhooks/hubspot" \
  -H "Content-Type: application/json" \
  -d '{"subscriptionType":"contact.creation"}' \
  -s -o /dev/null -w "%{http_code}\n"

# Test ClickUp webhook
echo -n "ClickUp... "
curl -X POST "$BASE_URL/webhooks/clickup" \
  -H "Content-Type: application/json" \
  -d '{"event":"taskCreated"}' \
  -s -o /dev/null -w "%{http_code}\n"

echo "All tests completed!"
```

Run:
```bash
chmod +x test_webhooks.sh
./test_webhooks.sh
```

Expected output:
```
Testing Lab-Verse Webhooks...
Grafana... 200
HubSpot... 200
ClickUp... 200
All tests completed!
```

---

## 8. Monitoring Webhook Events

### View Real-Time Events

```bash
# Follow logs
docker-compose -f docker-compose.production.yml logs -f api

# Check Redis for recent events
docker-compose -f docker-compose.production.yml exec redis redis-cli
> LRANGE hubspot:events 0 9
> LRANGE clickup:events 0 9
```

### Check Event Processing

```bash
# View processed webhooks in last hour
curl http://localhost/api/dashboard/summary | jq
```

---

## 9. Webhook URL Reference

Use these URLs when configuring webhooks:

| Platform   | Webhook URL                              |
|------------|------------------------------------------|
| Grafana    | `https://yourdomain.com/webhooks/grafana` |
| HubSpot    | `https://yourdomain.com/webhooks/hubspot` |
| ClickUp    | `https://yourdomain.com/webhooks/clickup` |
| DataDog    | `https://yourdomain.com/webhooks/datadog` |
| GitHub     | `https://yourdomain.com/webhooks/github`  |

**Important:** Replace `yourdomain.com` with your actual domain!

---

## 10. Troubleshooting

### Webhook Not Receiving Events

1. **Check URL is accessible from internet:**
   ```bash
   curl https://yourdomain.com/health
   ```

2. **Verify webhook is registered:**
   - Check platform's webhook configuration
   - Ensure URL is correct (no typos)

3. **Check logs for incoming requests:**
   ```bash
   docker-compose -f docker-compose.production.yml logs -f api | grep webhook
   ```

4. **Test webhook manually:**
   ```bash
   curl -X POST https://yourdomain.com/webhooks/hubspot \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

### Webhook Signature Validation Failing

1. **Verify secret is set correctly in .env:**
   ```bash
   echo $HUBSPOT_WEBHOOK_SECRET
   ```

2. **Check signature header name:**
   - HubSpot: `X-HubSpot-Signature`
   - ClickUp: `X-Signature`
   - GitHub: `X-Hub-Signature-256`

3. **Temporarily disable validation for testing:**
   - Remove signature validation in code
   - Test webhook
   - Re-enable validation

### Events Not Being Processed

1. **Check Redis connection:**
   ```bash
   docker-compose -f docker-compose.production.yml exec redis redis-cli ping
   ```

2. **Check worker processes:**
   ```bash
   docker-compose -f docker-compose.production.yml ps | grep api
   ```

3. **Monitor background task queue:**
   ```bash
   docker-compose -f docker-compose.production.yml exec redis redis-cli
   > LLEN clickup:events
   ```

---

## 11. Security Best Practices

### Webhook Secrets

1. **Generate strong secrets:**
   ```bash
   openssl rand -hex 32
   ```

2. **Store in environment variables:**
   - Never hardcode secrets
   - Use `.env` file (never commit to Git)
   - Use secret management in production (Vault, AWS Secrets Manager)

3. **Rotate regularly:**
   - Update secrets every 90 days
   - Update in both `.env` and platform

### IP Whitelisting

If your platform supports it, whitelist only your server's IP:

```
Platform → Webhook Settings → IP Whitelist
Add: <your-server-ip>
```

### SSL/TLS

Always use HTTPS for webhooks:
- Get SSL certificate (Let's Encrypt)
- Configure in Nginx
- Verify certificate is valid

---

## 12. Complete Setup Checklist

- [ ] All API keys added to `.env`
- [ ] Grafana webhook configured
- [ ] HubSpot webhook configured
- [ ] ClickUp webhook configured
- [ ] DataDog webhook configured
- [ ] GitHub webhook configured
- [ ] All webhook secrets set in `.env`
- [ ] Webhook test script passed
- [ ] Real events being received
- [ ] Events being processed correctly
- [ ] Monitoring dashboard showing data
- [ ] SSL certificates installed (production)
- [ ] IP whitelisting configured (if applicable)

---



1. Check logs: `docker-compose -f docker-compose.production.yml logs -f`
2. Review API documentation: `http://localhost/docs`
3. Test integrations: `curl http://localhost/health/integrations`
4. Create GitHub issue with logs and error messages

---

**Congratulations!** 🎉

Your Lab-Verse Monitoring System is now fully integrated with all platforms.