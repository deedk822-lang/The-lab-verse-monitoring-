# Complete Zapier Ayrshare Multi-Channel Distribution Setup

This guide will help you set up a comprehensive multi-channel content distribution system that integrates Zapier, Ayrshare, MailChimp, Perplexity AI, Manus AI, A2A, and MCP services for automated content generation and distribution.

## 🎯 Overview

Your system now supports:
- **Social Media**: Ayrshare (Twitter, Facebook, LinkedIn, Instagram, YouTube, TikTok, Telegram, Reddit)
- **Email Marketing**: MailChimp campaigns
- **Research Enhancement**: Perplexity AI with web search
- **Creative Writing**: Manus AI optimization
- **Cross-Platform Communication**: A2A (Slack, Teams, Discord, etc.)
- **Advanced AI**: MCP with Claude & Mistral AI

## 📋 Prerequisites

1. **Your existing AI Content Creation Suite** (already deployed)
2. **Zapier account** (free or paid)
3. **API keys** for the services you want to use

## 🔧 Step 1: Environment Configuration

### 1.1 Update your `.env` file with the following variables:

```bash
# Ayrshare (Social Media) - REQUIRED
AYRSHARE_API_KEY=your_ayrshare_api_key_here

# MailChimp (Email Marketing) - REQUIRED for email distribution
MAILCHIMP_API_KEY=your_mailchimp_api_key_here
MAILCHIMP_SERVER_PREFIX=us1  # Check your MailChimp account for correct prefix
MAILCHIMP_LIST_ID=your_mailchimp_list_id_here
MAILCHIMP_REPLY_TO=noreply@yourdomain.com

# Email Settings
EMAIL_FROM_NAME=AI Content Suite
EMAIL_REPLY_TO=noreply@yourdomain.com

# Perplexity AI (Research & Web Search) - OPTIONAL
PERPLEXITY_API_KEY=your_perplexity_api_key_here
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online

# Manus AI (Creative Writing) - OPTIONAL
MANUS_API_KEY=your_manus_api_key_here
MANUS_BASE_URL=https://api.manus.ai/v1
MANUS_MODEL=manus-creative-v1

# A2A (Cross-Platform Communication) - OPTIONAL
A2A_API_KEY=your_a2a_api_key_here
A2A_SECRET_KEY=your_a2a_secret_key_here
A2A_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
A2A_TEAMS_WEBHOOK=https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK

# MCP with Claude & Mistral - OPTIONAL
CLAUDE_API_KEY=your_claude_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large-latest
```

### 1.2 Get API Keys:

#### **Ayrshare (Required)**
1. Visit [Ayrshare](https://app.ayrshare.com/)
2. Sign up and connect your social media accounts
3. Get your API key from the dashboard

#### **MailChimp (Required for email)**
1. Visit [MailChimp](https://mailchimp.com/)
2. Go to Account → Extras → API keys
3. Create a new API key
4. Find your server prefix (e.g., `us1`, `us2`) in the API key
5. Create an audience/list and get the List ID

#### **Optional Services**
- **Perplexity AI**: [Sign up here](https://www.perplexity.ai/)
- **Manus AI**: [Sign up here](https://manus.ai/)
- **Claude AI**: [Anthropic Console](https://console.anthropic.com/)
- **Mistral AI**: [Mistral Console](https://console.mistral.ai/)

## 🔧 Step 2: Zapier Webhook Setup

### 2.1 Create Your Zap
1. Go to [Zapier](https://zapier.com/) and click **Create Zap**
2. **Trigger App**: Select **Webhooks by Zapier**
3. **Trigger Event**: Choose **Catch Hook**
4. Copy your webhook URL (e.g., `https://hooks.zapier.com/hooks/catch/24571038/uivaw0l/`)

### 2.2 Configure the Action
1. **Action App**: Select **Webhooks by Zapier**
2. **Action Event**: Choose **Custom Request**
3. **Method**: POST
4. **URL**: `https://YOUR_FLY_IO_APP_NAME.fly.dev/api/ayrshare/ayr`
   - Replace `YOUR_FLY_IO_APP_NAME` with your actual app name

### 2.3 Configure Headers
```
Content-Type: application/json
x-api-key: your_secure_api_key_here
```

### 2.4 Configure Data (JSON)
```json
{
  "topic": "{{trigger.topic}}",
  "platforms": "{{trigger.platforms}}",
  "audience": "{{trigger.audience}}",
  "tone": "{{trigger.tone}}",
  "provider": "{{trigger.provider}}",
  "includeEmail": "{{trigger.includeEmail}}",
  "emailSubject": "{{trigger.emailSubject}}"
}
```

## 🧪 Step 3: Testing Your Setup

### 3.1 Test Individual Services
```bash
# Test Ayrshare
curl -X GET "https://YOUR_APP.fly.dev/api/test/ayrshare" \
  -H "x-api-key: your_api_key"

# Test MailChimp
curl -X GET "https://YOUR_APP.fly.dev/api/ayrshare/test/mailchimp" \
  -H "x-api-key: your_api_key"

# Test Full Workflow
curl -X GET "https://YOUR_APP.fly.dev/api/ayrshare/test/workflow" \
  -H "x-api-key: your_api_key"
```

### 3.2 Test Zapier Webhook
```bash
curl -X POST "https://hooks.zapier.com/hooks/catch/24571038/uivaw0l/" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI Technology Trends 2024",
    "platforms": "twitter,linkedin,facebook",
    "audience": "tech professionals",
    "tone": "professional",
    "provider": "google",
    "includeEmail": true,
    "emailSubject": "Latest AI Trends - Weekly Update"
  }'
```

### 3.3 Test Manual Posting
```bash
# Social Media Only
curl -X POST "https://YOUR_APP.fly.dev/api/ayrshare/post" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_api_key" \
  -d '{
    "content": "Test post from AI Content Suite! 🚀 #AI #Technology",
    "platforms": "twitter,linkedin"
  }'

# Email Only
curl -X POST "https://YOUR_APP.fly.dev/api/ayrshare/email" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_api_key" \
  -d '{
    "subject": "Test Email Campaign",
    "content": "This is a test email from AI Content Suite!"
  }'
```

## 🚀 Step 4: Advanced Features

### 4.1 Multi-Provider Content Generation
Your system can now use multiple AI providers:
- **Google Gemini**: Default, great for general content
- **Perplexity AI**: Best for research-heavy content with web search
- **Manus AI**: Excellent for creative and engaging content
- **Claude AI**: Superior for complex reasoning and analysis
- **Mistral AI**: Great for multilingual content

### 4.2 Enhanced Workflow Options
```json
{
  "topic": "Sustainable Technology Innovation",
  "platforms": "twitter,linkedin,facebook,instagram",
  "audience": "business leaders",
  "tone": "authoritative",
  "provider": "perplexity",  // Use Perplexity for research
  "includeEmail": true,
  "emailSubject": "Sustainable Tech: What Leaders Need to Know",
  "enhanceWithManus": true,    // Optional: enhance with Manus AI
  "useWebSearch": true,        // Optional: include latest web data
  "multiLingual": ["es", "fr"], // Optional: generate translations
  "notifyTeams": true          // Optional: send A2A notifications
}
```

### 4.3 Real-Time Monitoring
Your app provides WebSocket updates for real-time progress monitoring:
```javascript
// Frontend JavaScript for real-time updates
const socket = io('https://YOUR_APP.fly.dev');

socket.on('ayrshare_progress', (data) => {
  console.log('Progress:', data.status, data.message);
  // Update your UI with progress information
});
```

## 📊 Step 5: Monitoring and Analytics

### 5.1 Check System Health
```bash
curl -X GET "https://YOUR_APP.fly.dev/api/test/health"
```

### 5.2 View Logs
```bash
# If deployed on Fly.io
fly logs -a YOUR_APP_NAME

# Or check your application logs
tail -f logs/app.log
```

### 5.3 Get Post Analytics
```bash
# Get Ayrshare post status
curl -X GET "https://YOUR_APP.fly.dev/api/ayrshare/status/POST_ID" \
  -H "x-api-key: your_api_key"
```

## 🛠️ Troubleshooting

### Common Issues:

1. **"API key not configured"**
   - Ensure your `.env` file has the correct API keys
   - Restart your application after updating environment variables

2. **"Webhook not triggering"**
   - Verify the webhook URL matches exactly
   - Check Zapier task history for errors
   - Ensure your Fly.io app is running

3. **"Social media posting failed"**
   - Check if social accounts are connected in Ayrshare
   - Verify platform-specific content requirements
   - Check Ayrshare dashboard for connection status

4. **"Email campaign failed"**
   - Verify MailChimp API key and server prefix
   - Ensure the list ID exists and is active
   - Check MailChimp account status

### Debug Mode:
```bash
# Enable detailed logging
LOG_LEVEL=debug npm start
```

## 🎯 Expected Workflow

1. **Trigger**: Zapier receives webhook with content parameters
2. **Research** (if using Perplexity): Latest web data is gathered
3. **Generation**: AI creates optimized content using your preferred provider
4. **Enhancement** (if using Manus): Content is optimized for engagement
5. **Distribution**: Content is posted to:
   - Social media platforms via Ayrshare
   - Email subscribers via MailChimp
   - Team channels via A2A (optional)
6. **Monitoring**: Real-time progress updates via WebSocket
7. **Analytics**: Performance tracking and reporting

## 📈 Performance Expectations

- **Content Generation**: 10-30 seconds (depending on AI provider)
- **Social Media Posting**: 5-15 seconds
- **Email Campaign**: 10-30 seconds
- **Total Workflow**: 30-90 seconds end-to-end
- **Concurrent Requests**: Supports multiple simultaneous workflows

## 🔐 Security Best Practices

1. **Use strong API keys** and rotate them regularly
2. **Enable rate limiting** (already configured)
3. **Use HTTPS** for all communications (already enforced)
4. **Monitor logs** for suspicious activity
5. **Keep dependencies updated**

## 📞 Support Resources

- **Ayrshare**: [Help Center](https://help.ayrshare.com/)
- **MailChimp**: [Support](https://mailchimp.com/help/)
- **Zapier**: [Help Center](https://help.zapier.com/)
- **Your App Logs**: Check `/health` endpoint for system status

---

**🎉 Congratulations!** Your multi-channel AI content distribution system is now ready to automatically generate, optimize, and distribute content across all your channels with just a single webhook trigger.
