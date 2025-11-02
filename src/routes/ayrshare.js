// src/routes/ayrshare.js
import express from 'express';
import { body, validationResult } from 'express-validator';
import ayrshareService from '../services/ayrshareService.js';
import mailchimpService from '../services/mailchimpService.js';
import { ContentGenerator } from '../services/ContentGenerator.js';
import { logger } from '../utils/logger.js';
import { io } from '../server.js';

const router = express.Router();
const contentGenerator = new ContentGenerator();

router.post('/ayr', [
  body('topic').notEmpty().withMessage('Topic is required'),
  body('platforms').notEmpty().withMessage('Platforms are required')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      logger.warn('Validation failed:', errors.array());
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { 
      topic, 
      platforms, 
      audience = 'general audience',
      tone = 'professional',
      provider = 'mistral',
      keywords = [],
      length = 'medium',
      includeEmail = false,
      emailSubject
    } = req.body;
    
    const startTime = Date.now();
    
    logger.info('Zapier webhook triggered:', {
      topic,
      platforms,
      includeEmail
    });

    io.emit('ayrshare_progress', {
      status: 'started',
      message: 'Processing webhook request',
      timestamp: new Date().toISOString()
    });

    // Generate content
    io.emit('ayrshare_progress', {
      status: 'generating',
      message: 'Generating AI content',
      timestamp: new Date().toISOString()
    });

    const contentResult = await contentGenerator.generateContent({
      topic,
      audience,
      tone,
      keywords,
      length,
      options: {
        optimizeForSocial: true,
        optimizeForEmail: includeEmail,
        platforms: platforms.split(',').map(p => p.trim())
      }
    });
    
    if (!contentResult.success) {
      throw new Error(`Content generation failed: ${contentResult.error}`);
    }

    const { content } = contentResult;
    
    logger.info('Content generated:', {
      length: content.length,
      processingTime: Date.now() - startTime
    });

    const results = {
      social: null,
      email: null
    };

    // Post to social media
    io.emit('ayrshare_progress', {
      status: 'posting_social',
      message: 'Posting to social media',
      timestamp: new Date().toISOString()
    });

    const postResult = await ayrshareService.post({
      post: content,
      platforms: platforms
    });

    results.social = postResult;

    // Send email if requested
    if (includeEmail) {
      io.emit('ayrshare_progress', {
        status: 'sending_email',
        message: 'Sending email campaign',
        timestamp: new Date().toISOString()
      });

      const emailResult = await mailchimpService.createAndSendCampaign({
        subject: emailSubject || `${topic} - Update`,
        content: content,
        sendNow: true
      });

      results.email = emailResult;
    }
    
    const totalTime = Date.now() - startTime;
    const socialSuccess = postResult.success;
    const emailSuccess = !includeEmail || results.email?.success;
    const overallSuccess = socialSuccess && emailSuccess;

    if (overallSuccess) {
      io.emit('ayrshare_progress', {
        status: 'completed',
        message: 'Distribution completed successfully',
        totalTime,
        timestamp: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Content distributed successfully',
        data: {
          content: content.substring(0, 200) + '...',
          contentLength: content.length,
          processingTime: totalTime,
          distribution: {
            social: {
              success: socialSuccess,
              postId: postResult.data?.id,
              platforms: postResult.platforms
            },
            email: includeEmail ? {
              success: emailSuccess,
              campaignId: results.email?.data?.campaignId
            } : null
          }
        }
      });
    } else {
      const errors = [];
      if (!socialSuccess) errors.push(`Social: ${postResult.error}`);
      if (includeEmail && !emailSuccess) errors.push(`Email: ${results.email?.error}`);
      throw new Error(`Distribution failed - ${errors.join(', ')}`);
    }

  } catch (error) {
    logger.error('Webhook processing failed:', {
      error: error.message,
      stack: error.stack
    });

    io.emit('ayrshare_progress', {
      status: 'error',
      message: error.message,
      timestamp: new Date().toISOString()
    });

    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Keep all other routes (test, status, etc.) as they were
router.get('/test', async (req, res) => {
  try {
    const isConnected = await ayrshareService.testConnection();
    res.json({
      success: isConnected,
      message: isConnected ? 'Ayrshare connected' : 'Ayrshare not configured',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/test/mailchimp', async (req, res) => {
  try {
    const isConnected = await mailchimpService.testConnection();
    res.json({
      success: isConnected,
      message: isConnected ? 'MailChimp connected' : 'MailChimp not configured',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/test/workflow', async (req, res) => {
  try {
    const ayrshareOk = await ayrshareService.testConnection();
    const mailchimpOk = await mailchimpService.testConnection();
    
    res.json({
      success: ayrshareOk || mailchimpOk,
      services: {
        ayrshare: ayrshareOk,
        mailchimp: mailchimpOk
      },
      message: ayrshareOk && mailchimpOk ? 'All systems ready' : 'Some services not configured',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;