import express from 'express';
import { body, validationResult } from 'express-validator';
import ayrshareService from '../services/ayrshareService.js';
import mailchimpService from '../services/mailchimpService.js';
import { ContentGenerator } from '../services/ContentGenerator.js';
import { logger } from '../utils/logger.js';
import { io } from '../server.js';

const router = express.Router();
const contentGenerator = new ContentGenerator();

/**
 * Zapier webhook endpoint for Ayrshare auto-posting with MailChimp integration
 * This endpoint receives data from Zapier and triggers content generation + posting to social + email
 */
router.post('/ayr', [
  body('topic').notEmpty().withMessage('Topic is required'),
  body('platforms').notEmpty().withMessage('Platforms are required')
], async (req, res) => {
  try {
    // Log incoming request for debugging
    logger.info('Zapier webhook received:', {
      body: req.body,
      headers: req.headers
    });

    // Check for validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { 
      topic, 
      platforms, 
      audience, 
      tone, 
      mediaType, 
      provider, 
      keywords, 
      length,
      includeEmail = true,
      emailSubject
    } = req.body;
    
    const startTime = Date.now();
    
    logger.info('Multi-channel auto-posting triggered:', {
      topic,
      platforms,
      audience,
      tone,
      mediaType: mediaType || 'text',
      provider: provider || 'google',
      includeEmail
    });

    // Emit progress update via WebSocket
    io.emit('ayrshare_progress', {
      status: 'started',
      message: 'Content generation started for multi-channel distribution',
      timestamp: new Date().toISOString()
    });

    // Step 1: Generate content using your existing AI services
    const contentRequest = {
      topic,
      audience: audience || 'general audience',
      tone: tone || 'professional',
      mediaType: mediaType || 'text',
      provider: provider || 'google',
      keywords: keywords || [],
      length: length || 'medium',
      options: {
        optimizeForSocial: true,
        optimizeForEmail: includeEmail,
        includeTags: true,
        platforms: platforms.split(',').map(p => p.trim())
      }
    };

    logger.info('Generating content with parameters:', contentRequest);
    
    // Emit progress update
    io.emit('ayrshare_progress', {
      status: 'generating',
      message: 'Generating content with AI',
      timestamp: new Date().toISOString()
    });

    const contentResult = await contentGenerator.generateContent(contentRequest);
    
    if (!contentResult.success) {
      throw new Error(`Content generation failed: ${contentResult.error}`);
    }

    const { content, metadata } = contentResult;
    
    logger.info('Content generated successfully:', {
      contentLength: content.length,
      provider: contentResult.provider,
      processingTime: Date.now() - startTime
    });

    // Initialize results object
    const results = {
      social: null,
      email: null
    };

    // Step 2: Post to social media via Ayrshare
    io.emit('ayrshare_progress', {
      status: 'posting_social',
      message: 'Posting to social media platforms',
      content: content.substring(0, 100) + '...',
      timestamp: new Date().toISOString()
    });

    const postingParams = {
      post: content,
      platforms: platforms,
      options: {
        shortenLinks: true,
        mediaDescription: metadata?.title || topic
      }
    };

    // Add media URL if available
    if (metadata?.mediaUrl) {
      postingParams.mediaUrl = metadata.mediaUrl;
    }

    const postResult = await ayrshareService.post(postingParams);
    results.social = postResult;

    // Step 3: Send to MailChimp if email is included
    if (includeEmail) {
      io.emit('ayrshare_progress', {
        status: 'sending_email',
        message: 'Creating and sending email campaign',
        timestamp: new Date().toISOString()
      });

      const emailParams = {
        subject: emailSubject || `${topic} - Latest Update`,
        content: content,
        fromName: process.env.EMAIL_FROM_NAME || 'AI Content Suite',
        replyTo: process.env.EMAIL_REPLY_TO || process.env.MAILCHIMP_REPLY_TO,
        sendNow: true
      };

      const emailResult = await mailchimpService.createAndSendCampaign(emailParams);
      results.email = emailResult;
    }
    
    const totalTime = Date.now() - startTime;
    
    // Determine overall success
    const socialSuccess = postResult.success;
    const emailSuccess = !includeEmail || results.email?.success;
    const overallSuccess = socialSuccess && emailSuccess;

    if (overallSuccess) {
      logger.info('Multi-channel posting completed successfully:', {
        social: {
          postId: postResult.data?.id,
          platforms: postResult.platforms
        },
        email: includeEmail ? {
          campaignId: results.email?.data?.campaignId,
          sent: results.email?.data?.sent
        } : 'skipped',
        totalTime: `${totalTime}ms`
      });

      // Emit success update
      io.emit('ayrshare_progress', {
        status: 'completed',
        message: `Content distributed successfully across ${includeEmail ? 'social media and email' : 'social media'}`,
        results: {
          social: {
            postId: postResult.data?.id,
            platforms: postResult.platforms
          },
          email: includeEmail ? {
            campaignId: results.email?.data?.campaignId,
            sent: results.email?.data?.sent
          } : null
        },
        totalTime,
        timestamp: new Date().toISOString()
      });

      res.json({
        success: true,
        message: `Content generated and distributed successfully across ${includeEmail ? 'social media and email channels' : 'social media channels'}`,
        data: {
          content: content.substring(0, 200) + (content.length > 200 ? '...' : ''),
          contentLength: content.length,
          processingTime: totalTime,
          provider: contentResult.provider,
          distribution: {
            social: {
              success: socialSuccess,
              postId: postResult.data?.id,
              platforms: postResult.platforms,
              error: postResult.error || null
            },
            email: includeEmail ? {
              success: emailSuccess,
              campaignId: results.email?.data?.campaignId,
              sent: results.email?.data?.sent,
              error: results.email?.error || null
            } : null
          }
        }
      });
    } else {
      const errors = [];
      if (!socialSuccess) errors.push(`Social media: ${postResult.error}`);
      if (includeEmail && !emailSuccess) errors.push(`Email: ${results.email?.error}`);
      
      throw new Error(`Distribution failed - ${errors.join(', ')}`);
    }

  } catch (error) {
    logger.error('Multi-channel auto-posting failed:', {
      error: error.message,
      stack: error.stack,
      body: req.body
    });

    // Emit error update
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

/**
 * Get post status endpoint
 */
router.get('/status/:postId', async (req, res) => {
  try {
    const { postId } = req.params;
    const result = await ayrshareService.getPostStatus(postId);
    
    res.json(result);
  } catch (error) {
    logger.error('Failed to get post status:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Test Ayrshare connection endpoint
 */
router.get('/test', async (req, res) => {
  try {
    const isConnected = await ayrshareService.testConnection();
    const profile = isConnected ? await ayrshareService.getUserProfile() : null;
    
    res.json({
      success: isConnected,
      message: isConnected ? 'Ayrshare connection successful' : 'Ayrshare connection failed',
      profile: profile?.data || null,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Ayrshare test failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Test MailChimp connection endpoint
 */
router.get('/test/mailchimp', async (req, res) => {
  try {
    const isConnected = await mailchimpService.testConnection();
    const listInfo = isConnected ? await mailchimpService.getListInfo() : null;
    
    res.json({
      success: isConnected,
      message: isConnected ? 'MailChimp connection successful' : 'MailChimp connection failed',
      listInfo: listInfo?.data || null,
      configured: {
        apiKey: !!process.env.MAILCHIMP_API_KEY,
        serverPrefix: !!process.env.MAILCHIMP_SERVER_PREFIX,
        listId: !!process.env.MAILCHIMP_LIST_ID
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('MailChimp test failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Test full multi-channel workflow
 */
router.get('/test/workflow', async (req, res) => {
  try {
    const ayrshareConnected = await ayrshareService.testConnection();
    const mailchimpConnected = await mailchimpService.testConnection();
    
    const tests = {
      ayrshare: {
        connected: ayrshareConnected,
        configured: !!process.env.AYRSHARE_API_KEY
      },
      mailchimp: {
        connected: mailchimpConnected,
        configured: {
          apiKey: !!process.env.MAILCHIMP_API_KEY,
          serverPrefix: !!process.env.MAILCHIMP_SERVER_PREFIX,
          listId: !!process.env.MAILCHIMP_LIST_ID
        }
      }
    };

    const allConfigured = tests.ayrshare.configured && 
                         tests.mailchimp.configured.apiKey && 
                         tests.mailchimp.configured.serverPrefix && 
                         tests.mailchimp.configured.listId;
                         
    const allConnected = ayrshareConnected && mailchimpConnected;
    
    res.json({
      success: allConnected,
      message: allConnected ? 'All services ready for multi-channel distribution' : 'Some services are not ready',
      tests,
      ready: {
        configured: allConfigured,
        connected: allConnected,
        readyForProduction: allConfigured && allConnected
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Workflow test failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Manual post endpoint for testing social media only
 */
router.post('/post', [
  body('content').notEmpty().withMessage('Content is required'),
  body('platforms').notEmpty().withMessage('Platforms are required')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { content, platforms, mediaUrl } = req.body;
    
    const result = await ayrshareService.post({
      post: content,
      platforms,
      mediaUrl
    });
    
    res.json(result);
  } catch (error) {
    logger.error('Manual post failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Manual email campaign endpoint for testing MailChimp only
 */
router.post('/email', [
  body('subject').notEmpty().withMessage('Email subject is required'),
  body('content').notEmpty().withMessage('Email content is required')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { subject, content, fromName, replyTo, sendNow = true } = req.body;
    
    const result = await mailchimpService.createAndSendCampaign({
      subject,
      content,
      fromName,
      replyTo,
      sendNow
    });
    
    res.json(result);
  } catch (error) {
    logger.error('Manual email campaign failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;