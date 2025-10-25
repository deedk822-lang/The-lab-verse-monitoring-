# 🔄 Zapier Canvas Complete Configuration Guide

## 📋 Overview

This document provides the complete configuration for integrating your AI Content Creation Suite with Zapier Canvas. The integration enables automated content generation, SEO optimization, and multi-platform distribution.

**Canvas URL**: https://zapier.com/app/canvas/2073725c-c81c-40ca-ba35-1a483bc8b60f

---

## ✅ Pre-Configuration Checklist

### Server Requirements
- [x] Server running and accessible
- [x] All API endpoints operational (/api/content/generate, /api/content/seo, /api/content/social)
- [x] Health endpoint responding at `/health`
- [x] API key authentication configured
- [x] GitHub Action webhook setup

### Required Environment Variables
```bash
# In your production server .env file:
PORT=3000
NODE_ENV=production
API_KEY=your_secure_api_key_here
WEBHOOK_SECRET=your_webhook_secret_here

# At least one AI provider configured:
GOOGLE_API_KEY=your_google_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here
```

### Zapier Requirements
- Zapier account with access to:
  - Webhooks by Zapier
  - Storage by Zapier
  - Formatter by Zapier
  - Your distribution apps (Slack, Google Sheets, Notion, etc.)

---

## 🎯 Canvas Architecture

```
GitHub Action Trigger
        ↓
[1] Catch Hook (Zapier Trigger)
        ↓
[2] Parse JSON (Formatter)
        ↓
[3] Store Run Context (Storage)
        ↓
    ┌───┴───┐
    ↓       ↓       ↓
[4] Generate  [5] SEO  [6] Social
 Content    Optimize  Media
    ↓       ↓       ↓
    └───┬───┘
        ↓
[7] Distribution (Slack, Sheets, Notion, etc.)
        ↓
[8] Analytics (GA4)
        ↓
[9] Completion Notification
```

---

## 🔧 Step-by-Step Zap Configuration

### Step 1: Catch Hook (Trigger)

**App**: Webhooks by Zapier  
**Action**: Catch Hook

1. Create a new Zap in your Canvas
2. Select "Webhooks by Zapier" as trigger
3. Choose "Catch Hook"
4. Copy the generated webhook URL
5. **IMPORTANT**: Update your GitHub Action with the new URL

**Update GitHub Action**:
```yaml
# File: .github/workflows/trigger-content.yml
# Line 50: Replace with your NEW webhook URL
WEBHOOK_URL: "https://hooks.zapier.com/hooks/catch/YOUR_ACCOUNT_ID/YOUR_HOOK_ID/"
```

**Test the trigger**:
```bash
# Run this from your terminal to test:
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Content",
    "content": "This is a test",
    "source": "Manual Test",
    "repository": "test/repo",
    "commit": "abc123",
    "event_type": "manual",
    "branch": "main",
    "actor": "tester",
    "timestamp": "2025-10-25T12:00:00Z",
    "workflow_run_id": "test123"
  }'
```

---

### Step 2: Parse JSON (Formatter)

**App**: Formatter by Zapier  
**Action**: Utilities → Text → Parse JSON

**Configuration**:
- **Input**: Raw Body from Step 1 (Catch Hook)
- **Purpose**: Extract structured fields from webhook payload

**Field Mappings** (these will be available after parsing):
- `title` → Content title
- `content` → Raw content
- `repository` → GitHub repo name
- `commit` → Commit SHA
- `workflow_run_id` → Unique run identifier
- `timestamp` → Event timestamp
- `actor` → GitHub username
- `branch` → Git branch name

---

### Step 3: Store Run Context (Storage)

**App**: Storage by Zapier  
**Action**: Set Value

**Configuration**:
- **Key**: `content:run:{{workflow_run_id}}`
- **Value**: JSON object with base fields:
```json
{
  "title": "{{title}}",
  "repository": "{{repository}}",
  "commit": "{{commit}}",
  "status": "processing",
  "started_at": "{{timestamp}}",
  "actor": "{{actor}}"
}
```

---

### Step 4: Generate Content (Core AI)

**App**: Webhooks by Zapier  
**Action**: POST

**Configuration**:
- **URL**: `https://YOUR_DOMAIN.com/api/content/generate`
- **Method**: POST
- **Headers**:
  ```
  Content-Type: application/json
  x-api-key: {{YOUR_API_KEY}}
  ```
- **Data** (JSON):
```json
{
  "topic": "{{title}}",
  "audience": "marketing professionals",
  "tone": "professional",
  "language": "en",
  "mediaType": "text",
  "provider": "google",
  "keywords": [],
  "length": "medium"
}
```

**Response Structure**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "content": "Generated content...",
    "metadata": {...}
  }
}
```

**Store Result**:
- Create another Storage step
- **Key**: `content:run:{{workflow_run_id}}:core`
- **Value**: `{{data}}`

---

### Step 5: SEO Optimization

**App**: Webhooks by Zapier  
**Action**: POST

**Configuration**:
- **URL**: `https://YOUR_DOMAIN.com/api/content/seo`
- **Method**: POST
- **Headers**:
  ```
  Content-Type: application/json
  x-api-key: {{YOUR_API_KEY}}
  ```
- **Data** (JSON):
```json
{
  "topic": "{{title}}",
  "content": "{{steps.generate.data.content}}",
  "provider": "google"
}
```

**Response Structure**:
```json
{
  "success": true,
  "data": {
    "title": "SEO-optimized title",
    "description": "Meta description",
    "keywords": ["keyword1", "keyword2"],
    "tags": ["tag1", "tag2"]
  }
}
```

**Store Result**:
- **Key**: `content:run:{{workflow_run_id}}:seo`
- **Value**: `{{data}}`

---

### Step 6: Social Media Posts

**App**: Webhooks by Zapier  
**Action**: POST

**Configuration**:
- **URL**: `https://YOUR_DOMAIN.com/api/content/social`
- **Method**: POST
- **Headers**:
  ```
  Content-Type: application/json
  x-api-key: {{YOUR_API_KEY}}
  ```
- **Data** (JSON):
```json
{
  "topic": "{{title}}",
  "content": "{{steps.generate.data.content}}",
  "platforms": ["twitter", "linkedin", "instagram"],
  "provider": "google"
}
```

**Response Structure**:
```json
{
  "success": true,
  "data": {
    "twitter": "Tweet text...",
    "linkedin": "LinkedIn post...",
    "instagram": "Instagram caption..."
  }
}
```

**Store Result**:
- **Key**: `content:run:{{workflow_run_id}}:social`
- **Value**: `{{data}}`

---

## 📤 Distribution Steps (Examples)

### Slack Notification

**App**: Slack  
**Action**: Send Channel Message

**Configuration**:
- **Channel**: #content (or your channel)
- **Message**:
```
🚀 *New AI Content Generated*

*Title*: {{title}}
*Repository*: {{repository}}
*Commit*: {{commit}}

*SEO Keywords*: {{steps.seo.data.keywords}}

*Social Media*:
• Twitter: {{steps.social.data.twitter}}
• LinkedIn: {{steps.social.data.linkedin}}

*Content ID*: {{steps.generate.data.id}}
*Run ID*: {{workflow_run_id}}
```

---

### Google Sheets

**App**: Google Sheets  
**Action**: Create Spreadsheet Row

**Configuration**:
- **Spreadsheet**: Your content tracking sheet
- **Worksheet**: Content Log
- **Columns**:
  - Timestamp: `{{timestamp}}`
  - Title: `{{title}}`
  - Repository: `{{repository}}`
  - Commit: `{{commit}}`
  - Content ID: `{{steps.generate.data.id}}`
  - SEO Keywords: `{{steps.seo.data.keywords}}`
  - Status: `Generated`
  - LinkedIn Copy: `{{steps.social.data.linkedin}}`
  - Instagram Copy: `{{steps.social.data.instagram}}`

---

### Notion Database

**App**: Notion  
**Action**: Create Database Item

**Configuration**:
- **Database**: Content Repository
- **Properties**:
  - Title: `{{title}}`
  - Status: `Generated`
  - Run ID: `{{workflow_run_id}}`
  - Repository: `{{repository}}`
  - Commit: `{{commit}}`
  - Created: `{{timestamp}}`
  - SEO Keywords: `{{steps.seo.data.keywords}}`
  - Content: `{{steps.generate.data.content}}`

---

### Buffer (Social Media Scheduling)

**App**: Buffer  
**Action**: Add to Queue

**For LinkedIn**:
- **Profile**: Your LinkedIn profile
- **Text**: `{{steps.social.data.linkedin}}`
- **Schedule**: Now or custom time

**For Instagram**:
- **Profile**: Your Instagram profile
- **Text**: `{{steps.social.data.instagram}}`
- **Schedule**: Now or custom time

---

### Gmail Draft

**App**: Gmail  
**Action**: Create Draft

**Configuration**:
- **To**: (leave empty or distribution list)
- **Subject**: `New Content: {{title}}`
- **Body**:
```html
<h2>{{title}}</h2>

<h3>Content Preview</h3>
<p>{{steps.generate.data.content}}</p>

<h3>SEO Details</h3>
<ul>
  <li>Title: {{steps.seo.data.title}}</li>
  <li>Description: {{steps.seo.data.description}}</li>
  <li>Keywords: {{steps.seo.data.keywords}}</li>
</ul>

<h3>Social Media Posts</h3>
<p><strong>LinkedIn:</strong> {{steps.social.data.linkedin}}</p>
<p><strong>Twitter:</strong> {{steps.social.data.twitter}}</p>
<p><strong>Instagram:</strong> {{steps.social.data.instagram}}</p>
```

---

## 📊 Analytics Integration

### Google Analytics 4 (GA4)

**App**: Webhooks by Zapier  
**Action**: POST

**Configuration**:
- **URL**: `https://www.google-analytics.com/mp/collect?measurement_id={{YOUR_GA4_MEASUREMENT_ID}}&api_secret={{YOUR_GA4_API_SECRET}}`
- **Method**: POST
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Data** (JSON):
```json
{
  "client_id": "{{workflow_run_id}}",
  "events": [
    {
      "name": "content_generated",
      "params": {
        "title": "{{title}}",
        "repository": "{{repository}}",
        "run_id": "{{workflow_run_id}}",
        "content_id": "{{steps.generate.data.id}}",
        "event_timestamp": "{{timestamp}}"
      }
    }
  ]
}
```

---

## ✅ Completion Step

**App**: Storage by Zapier  
**Action**: Set Value

**Configuration**:
- **Key**: `content:run:{{workflow_run_id}}:status`
- **Value**: `completed`

**Then**: Send final Slack notification
```
✅ *Content Pipeline Complete*

All steps finished successfully for: {{title}}
View results in Google Sheets, Notion, and Buffer queue.

Run ID: {{workflow_run_id}}
```

---

## 🧪 Testing Guide

### 1. Test Server Health

```bash
curl https://YOUR_DOMAIN.com/health
# Expected: {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### 2. Test API Endpoints Manually

**Generate Content**:
```bash
curl -X POST https://YOUR_DOMAIN.com/api/content/generate \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "topic": "Test Topic",
    "audience": "developers",
    "tone": "professional",
    "language": "en",
    "mediaType": "text",
    "provider": "google",
    "length": "medium"
  }'
```

**SEO**:
```bash
curl -X POST https://YOUR_DOMAIN.com/api/content/seo \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "topic": "Test Topic",
    "content": "Sample content for SEO analysis",
    "provider": "google"
  }'
```

**Social**:
```bash
curl -X POST https://YOUR_DOMAIN.com/api/content/social \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "topic": "Test Topic",
    "content": "Sample content for social media",
    "platforms": ["twitter", "linkedin", "instagram"],
    "provider": "google"
  }'
```

### 3. Test GitHub Action

**Method 1: Manual Trigger**
1. Go to GitHub → Actions → "Trigger AI Content Workflow"
2. Click "Run workflow"
3. Enter test title and content
4. Click "Run workflow"
5. Monitor Zapier Canvas for activity

**Method 2: Push Content File**
```bash
# Create a new markdown file in content/
echo "# Test Content" > content/test-$(date +%s).md
git add content/
git commit -m "Test: Trigger Zapier workflow"
git push
```

### 4. Verify End-to-End Flow

Check each destination:
- ✅ Zapier run completed without errors
- ✅ Slack channel received notification
- ✅ Google Sheets has new row
- ✅ Notion has new item
- ✅ Buffer queue updated (if configured)
- ✅ Gmail draft created (if configured)
- ✅ GA4 received event (check Real-time reports)
- ✅ Storage keys exist in Zapier Storage

---

## 🔐 Security Checklist

- [x] API key configured and secure (minimum 32 characters)
- [x] Webhook URL rotated from old/exposed URLs
- [x] HTTPS enforced on all endpoints
- [x] Rate limiting enabled (100 requests per 15 minutes)
- [x] API keys stored as environment variables (never committed)
- [x] Zapier uses secure credential storage
- [x] GitHub Actions uses repository secrets for sensitive data

---

## 🚨 Troubleshooting

### Webhook Not Receiving Data
1. Check GitHub Action logs for curl errors
2. Verify webhook URL is correct and active
3. Test webhook manually with curl
4. Check Zapier task history for received data

### API Endpoints Failing
1. Verify server is running and accessible
2. Check API key is correct
3. Verify AI provider keys are configured
4. Check server logs for errors
5. Test endpoints manually with curl

### Distribution Steps Failing
1. Verify app connections are active in Zapier
2. Check app permissions (Slack, Google Sheets, etc.)
3. Verify field mappings reference correct step data
4. Test each distribution step individually

### Storage Keys Not Found
1. Check Storage step ran successfully
2. Verify key naming format matches between steps
3. Check Zapier Storage dashboard for existing keys
4. Ensure workflow_run_id is being passed correctly

---

## 📈 Monitoring & Maintenance

### Regular Checks
- **Daily**: Review Zapier task history for errors
- **Weekly**: Check API endpoint response times
- **Monthly**: Rotate API keys and webhook URLs
- **Quarterly**: Audit storage usage and cleanup old runs

### Key Metrics to Track
- Zapier task success rate (target: >99%)
- API endpoint response time (target: <2s)
- Content generation quality score
- Distribution success rates per platform

---

## 📚 Additional Resources

- [API Documentation](/docs/API.md)
- [GitHub Actions Workflow](/.github/workflows/trigger-content.yml)
- [Environment Variables](/.env.example)
- [Zapier Canvas](https://zapier.com/app/canvas/2073725c-c81c-40ca-ba35-1a483bc8b60f)

---

## 🎯 Quick Reference

### Your Endpoints
```
Health:   GET  https://YOUR_DOMAIN.com/health
Generate: POST https://YOUR_DOMAIN.com/api/content/generate
SEO:      POST https://YOUR_DOMAIN.com/api/content/seo
Social:   POST https://YOUR_DOMAIN.com/api/content/social
```

### Required Headers
```
Content-Type: application/json
x-api-key: YOUR_API_KEY
```

### Sample Webhook Payload
```json
{
  "title": "Content Title",
  "content": "Content body",
  "source": "GitHub Actions",
  "repository": "owner/repo",
  "commit": "abc123",
  "event_type": "push",
  "branch": "main",
  "actor": "username",
  "timestamp": "2025-10-25T12:00:00Z",
  "workflow_run_id": "123456"
}
```

---

**Status**: ✅ Configuration guide complete and ready for implementation

**Last Updated**: 2025-10-25
