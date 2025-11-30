// api/inngest.js - Vercel Serverless Function for Inngest
// 28-Platform Distribution Pipeline via Inngest

import crypto from 'crypto';

// Platform configuration
const PLATFORMS = {
  // Social Media
  twitter: { enabled: true, api: 'twitter', name: 'Twitter/X' },
  linkedin: { enabled: true, api: 'linkedin', name: 'LinkedIn' },
  facebook: { enabled: true, api: 'facebook', name: 'Facebook' },
  instagram: { enabled: true, api: 'instagram', name: 'Instagram' },
  reddit: { enabled: true, api: 'reddit', name: 'Reddit' },
  pinterest: { enabled: true, api: 'pinterest', name: 'Pinterest' },
  tumblr: { enabled: true, api: 'tumblr', name: 'Tumblr' },
  
  // Developer Platforms
  medium: { enabled: true, api: 'medium', name: 'Medium' },
  devto: { enabled: true, api: 'dev.to', name: 'Dev.to' },
  hashnode: { enabled: true, api: 'hashnode', name: 'Hashnode' },
  
  // Messaging
  telegram: { enabled: true, api: 'telegram', name: 'Telegram' },
  whatsapp: { enabled: true, api: 'whatsapp', name: 'WhatsApp Business' },
  slack: { enabled: true, api: 'slack', name: 'Slack' },
  discord: { enabled: true, api: 'discord', name: 'Discord' },
  
  // Email Marketing
  mailchimp: { enabled: true, api: 'mailchimp', name: 'Mailchimp' },
  sendgrid: { enabled: true, api: 'sendgrid', name: 'SendGrid' },
  
  // Content Platforms
  wordpress: { enabled: true, api: 'wordpress', name: 'WordPress' },
  ghost: { enabled: true, api: 'ghost', name: 'Ghost' },
  substack: { enabled: true, api: 'substack', name: 'Substack' },
  
  // Video
  youtube: { enabled: true, api: 'youtube', name: 'YouTube Community' },
  tiktok: { enabled: true, api: 'tiktok', name: 'TikTok' },
  
  // Professional
  github: { enabled: true, api: 'github', name: 'GitHub' },
  notion: { enabled: true, api: 'notion', name: 'Notion' },
  
  // News
  hackernews: { enabled: true, api: 'hackernews', name: 'Hacker News' },
  
  // Other
  mastodon: { enabled: true, api: 'mastodon', name: 'Mastodon' },
  bluesky: { enabled: true, api: 'bluesky', name: 'Bluesky' },
  threads: { enabled: true, api: 'threads', name: 'Threads' },
  quora: { enabled: true, api: 'quora', name: 'Quora' }
};

/**
 * Verify webhook signature
 */
function verifySignature(payload, signature, secret) {
  if (!signature || !secret) return false;
  
  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(payload).digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}

/**
 * Generate unique run ID
 */
function generateRunId() {
  return `run_${Date.now()}_${crypto.randomBytes(8).toString('hex')}`;
}

/**
 * Simulate platform publishing (in production, connect to real APIs)
 */
async function publishToPlatform(platform, content) {
  const config = PLATFORMS[platform];
  
  if (!config || !config.enabled) {
    return {
      platform,
      status: 'skipped',
      message: 'Platform not enabled'
    };
  }
  
  // Simulate API call with realistic delay
  await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));
  
  // In production, this would call the actual platform APIs
  // For now, return mock success
  return {
    platform,
    name: config.name,
    status: 'success',
    url: `https://${platform}.com/post/${crypto.randomBytes(6).toString('hex')}`,
    timestamp: new Date().toISOString()
  };
}

/**
 * Send email campaign
 */
async function sendEmailCampaign(content) {
  // Simulate email campaign
  await new Promise(resolve => setTimeout(resolve, 200));
  
  return {
    service: 'mailchimp',
    status: 'sent',
    recipients: 1247,
    campaign_id: `camp_${crypto.randomBytes(6).toString('hex')}`,
    timestamp: new Date().toISOString()
  };
}

/**
 * Main Inngest handler
 */
export default async function handler(req, res) {
  // Handle OPTIONS for CORS
  if (req.method === 'OPTIONS') {
    return res.status(200).json({ ok: true });
  }
  
  // Only accept POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    // Verify webhook signature
    const signature = req.headers['x-webhook-signature'];
    const secret = process.env.WEBHOOK_SECRET || process.env.RANKYAK_SECRET;
    const rawBody = JSON.stringify(req.body);
    
    if (secret && !verifySignature(rawBody, signature, secret)) {
      console.error('Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Parse payload
    const { event, data } = req.body;
    
    if (!data || !data.title) {
      return res.status(400).json({ error: 'Invalid payload: missing title' });
    }
    
    console.log(`Processing distribution: ${data.title}`);
    
    // Generate run ID
    const runId = generateRunId();
    const startTime = Date.now();
    
    // Parse platforms
    const requestedPlatforms = data.platforms 
      ? data.platforms.split(',').map(p => p.trim().toLowerCase())
      : Object.keys(PLATFORMS);
    
    // Distribute to all platforms in parallel
    const results = await Promise.allSettled(
      requestedPlatforms.map(platform => publishToPlatform(platform, data))
    );
    
    // Send email if requested
    let emailResult = null;
    if (data.includeEmail) {
      try {
        emailResult = await sendEmailCampaign(data);
      } catch (error) {
        console.error('Email campaign error:', error);
        emailResult = { status: 'failed', error: error.message };
      }
    }
    
    // Process results
    const platformResults = results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          platform: requestedPlatforms[index],
          status: 'failed',
          error: result.reason?.message || 'Unknown error'
        };
      }
    });
    
    const successCount = platformResults.filter(r => r.status === 'success').length;
    const failedCount = platformResults.filter(r => r.status === 'failed').length;
    const skippedCount = platformResults.filter(r => r.status === 'skipped').length;
    
    const duration = Date.now() - startTime;
    
    // Return comprehensive response
    return res.status(200).json({
      success: true,
      runId,
      event: event || 'distribution',
      content: {
        title: data.title,
        slug: data.slug
      },
      stats: {
        total: platformResults.length,
        success: successCount,
        failed: failedCount,
        skipped: skippedCount,
        duration: `${duration}ms`
      },
      platforms: platformResults,
      email: emailResult,
      dashboard: `https://app.inngest.com/function/rankyak-publish/runs/${runId}`,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Inngest processing error:', error);
    
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}
