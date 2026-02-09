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
  body('platforms').notEmpty().withMessage('Platforms are required'),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array(),
      });
    }

    const {
      topic,
      platforms,
      audience = 'general audience',
      tone = 'professional',
      provider = 'mistral-local',
      keywords = [],
      length = 'medium',
      includeEmail = false,
      emailSubject,
    } = req.body;

    const startTime = Date.now();

    logger.info('Webhook received:', { topic, platforms, audience, tone });

    io.emit('ayrshare_progress', {
      status: 'started',
      message: 'Content generation started',
      timestamp: new Date().toISOString(),
    });

    // Generate content
    const contentRequest = {
      topic,
      audience,
      tone,
      provider,
      keywords,
      length,
      options: {
        optimizeForSocial: true,
        optimizeForEmail: includeEmail,
        platforms: platforms.split(',').map(p => p.trim()),
      },
    };

    logger.info('Generating content...');

    io.emit('ayrshare_progress', {
      status: 'generating',
      message: 'Generating content with AI',
      timestamp: new Date().toISOString(),
    });

    const contentResult = await contentGenerator.generateContent(contentRequest);

    if (!contentResult.success) {
      throw new Error(`Content generation failed: ${contentResult.error}`);
    }

    const { content } = contentResult;

    logger.info('Content generated:', { length: content.length });

    const results = {
      social: null,
      email: null,
    };

    // Post to social media
    io.emit('ayrshare_progress', {
      status: 'posting_social',
      message: 'Posting to social media',
      timestamp: new Date().toISOString(),
    });

    const postResult = await ayrshareService.post({
      post: content,
      platforms: platforms,
      options: {
        shortenLinks: true,
      },
    });

    results.social = postResult;

    // Send email if requested
    if (includeEmail) {
      io.emit('ayrshare_progress', {
        status: 'sending_email',
        message: 'Sending email campaign',
        timestamp: new Date().toISOString(),
      });

      const emailResult = await mailchimpService.createAndSendCampaign({
        subject: emailSubject || `${topic} - Latest Update`,
        content: content,
        fromName: process.env.EMAIL_FROM_NAME || 'AI Content Suite',
        replyTo: process.env.EMAIL_REPLY_TO || 'noreply@example.com',
        sendNow: true,
      });

      results.email = emailResult;
    }

    const totalTime = Date.now() - startTime;
    const socialSuccess = postResult.success;
    const emailSuccess = !includeEmail || results.email?.success;
    const overallSuccess = socialSuccess && emailSuccess;

    if (overallSuccess) {
      logger.info('Distribution completed:', {
        social: postResult.data?.id,
        email: results.email?.data?.campaignId,
        time: `${totalTime}ms`,
      });

      io.emit('ayrshare_progress', {
        status: 'completed',
        message: 'Content distributed successfully',
        totalTime,
        timestamp: new Date().toISOString(),
      });

      res.json({
        success: true,
        message: 'Content generated and distributed successfully',
        data: {
          content: content.substring(0, 200) + '...',
          contentLength: content.length,
          processingTime: totalTime,
          distribution: {
            social: {
              success: socialSuccess,
              postId: postResult.data?.id,
              platforms: postResult.platforms,
            },
            email: includeEmail ? {
              success: emailSuccess,
              campaignId: results.email?.data?.campaignId,
            } : null,
          },
        },
      });
    } else {
      const errors = [];
      if (!socialSuccess) {
        errors.push(`Social: ${postResult.error}`);
      }
      if (includeEmail && !emailSuccess) {
        errors.push(`Email: ${results.email?.error}`);
      }
      throw new Error(`Distribution failed - ${errors.join(', ')}`);
    }

  } catch (error) {
    logger.error('Webhook failed:', error);

    io.emit('ayrshare_progress', {
      status: 'error',
      message: error.message,
      timestamp: new Date().toISOString(),
    });

    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

router.get('/test', async (req, res) => {
  try {
    const isConnected = await ayrshareService.testConnection();
    const profile = isConnected ? await ayrshareService.getUserProfile() : null;

    res.json({
      success: isConnected,
      message: isConnected ? 'Ayrshare connected' : 'Ayrshare not connected',
      profile: profile?.data || null,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    logger.error('Test failed:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

router.get('/test/mailchimp', async (req, res) => {
  try {
    const isConnected = await mailchimpService.testConnection();
    const listInfo = isConnected ? await mailchimpService.getListInfo() : null;

    res.json({
      success: isConnected,
      message: isConnected ? 'MailChimp connected' : 'MailChimp not connected',
      listInfo: listInfo?.data || null,
      configured: {
        apiKey: !!process.env.MAILCHIMP_API_KEY,
        serverPrefix: !!process.env.MAILCHIMP_SERVER_PREFIX,
        listId: !!process.env.MAILCHIMP_LIST_ID,
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

router.get('/test/workflow', async (req, res) => {
  try {
    const ayrshareConnected = await ayrshareService.testConnection();
    const mailchimpConnected = await mailchimpService.testConnection();

    res.json({
      success: ayrshareConnected || mailchimpConnected,
      message: 'Service status checked',
      services: {
        ayrshare: {
          connected: ayrshareConnected,
          configured: !!process.env.AYRSHARE_API_KEY,
        },
        mailchimp: {
          connected: mailchimpConnected,
          configured: {
            apiKey: !!process.env.MAILCHIMP_API_KEY,
            serverPrefix: !!process.env.MAILCHIMP_SERVER_PREFIX,
            listId: !!process.env.MAILCHIMP_LIST_ID,
          },
        },
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    logger.error('Workflow test failed:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

export default router;
