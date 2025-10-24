import express from 'express';
import axios from 'axios';
import logger from '../utils/logger.js';

const router = express.Router();

// Webhook endpoint for background agents to trigger Zapier
router.post('/background-agent-webhook', async (req, res) => {
  try {
    const { 
      agentId, 
      action, 
      data, 
      priority = 'normal',
      zapierWebhookUrl 
    } = req.body;

    // Validate required fields
    if (!agentId || !action || !data) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'agentId, action, and data are required'
      });
    }

    // Use provided webhook URL or default from environment
    const webhookUrl = zapierWebhookUrl || process.env.ZAPIER_WEBHOOK_URL;
    
    if (!webhookUrl) {
      return res.status(400).json({
        error: 'No Zapier webhook URL provided',
        message: 'Either provide zapierWebhookUrl in request or set ZAPIER_WEBHOOK_URL environment variable'
      });
    }

    // Prepare payload for Zapier
    const zapierPayload = {
      agent_id: agentId,
      action: action,
      data: data,
      priority: priority,
      timestamp: new Date().toISOString(),
      source: 'background_agent',
      metadata: {
        processing_time: Date.now(),
        agent_version: process.env.AGENT_VERSION || '1.0.0',
        server: process.env.SERVER_NAME || 'lab-verse'
      }
    };

    // Send to Zapier webhook
    const zapierResponse = await axios.post(webhookUrl, zapierPayload, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Lab-Verse-Background-Agent/1.0',
        'X-Webhook-Secret': process.env.WEBHOOK_SECRET || ''
      },
      timeout: 10000
    });

    logger.info('Background agent webhook triggered successfully', {
      agentId,
      action,
      zapierStatus: zapierResponse.status,
      webhookUrl: webhookUrl.replace(/\/[^\/]*$/, '/***') // Mask webhook URL in logs
    });

    res.json({
      success: true,
      message: 'Background agent webhook triggered successfully',
      zapier_response: zapierResponse.data,
      agent_id: agentId,
      action: action,
      timestamp: zapierPayload.timestamp
    });

  } catch (error) {
    logger.error('Background agent webhook failed', {
      error: error.message,
      agentId: req.body.agentId,
      action: req.body.action,
      stack: error.stack
    });

    res.status(500).json({
      success: false,
      error: 'Failed to trigger Zapier webhook',
      message: error.message,
      agent_id: req.body.agentId
    });
  }
});

// Health check endpoint for background agent webhook
router.get('/background-agent-webhook/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'background-agent-webhook',
    timestamp: new Date().toISOString(),
    version: process.env.AGENT_VERSION || '1.0.0'
  });
});

// Get webhook configuration
router.get('/background-agent-webhook/config', (req, res) => {
  res.json({
    webhook_url_configured: !!process.env.ZAPIER_WEBHOOK_URL,
    agent_version: process.env.AGENT_VERSION || '1.0.0',
    server_name: process.env.SERVER_NAME || 'lab-verse',
    supported_actions: [
      'ai_content_generation',
      'send_notification',
      'sync_data',
      'general_processing'
    ],
    supported_priorities: ['low', 'normal', 'high', 'urgent']
  });
});

export default router;