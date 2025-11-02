import express from 'express';
import { body, validationResult } from 'express-validator';
import ayrshareService from '../services/ayrshareService.js';
import { ContentGenerator } from '../services/contentGenerator.js';
import { logger } from '../utils/logger.js';
import { io } from '../server.js';

const router = express.Router();
const contentGenerator = new ContentGenerator();

/**
 * Zapier webhook endpoint for Ayrshare auto-posting
 * This endpoint receives data from Zapier and triggers content generation + posting
 */
router.post('/ayr', [
  body('topic').notEmpty().withMessage('Topic is required'),
  body('platforms').notEmpty().withMessage('Platforms are required')
], async (req, res) => {
  try {
    // Check for validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { topic, platforms, audience, tone, mediaType, provider, keywords, length } = req.body;
    const startTime = Date.now();
    
    logger.info('Ayrshare auto-posting triggered:', {
      topic,
      platforms,
      audience,
      tone,
      mediaType: mediaType || 'text',
      provider: provider || 'google'
    });

    // Emit progress update via WebSocket
    io.emit('ayrshare_progress', {
      status: 'started',
      message: 'Content generation started',
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

    // Emit progress update
    io.emit('ayrshare_progress', {
      status: 'posting',
      message: 'Posting to social media platforms',
      content: content.substring(0, 100) + '...',
      timestamp: new Date().toISOString()
    });

    // Step 2: Post to social media via Ayrshare
    const postingParams = {
      post: content,
      platforms: platforms,
      options: {
        // Add any platform-specific options
        shortenLinks: true,
        mediaDescription: metadata?.title || topic
      }
    };

    // Add media URL if available
    if (metadata?.mediaUrl) {
      postingParams.mediaUrl = metadata.mediaUrl;
    }

    const postResult = await ayrshareService.post(postingParams);
    
    const totalTime = Date.now() - startTime;
    
    if (postResult.success) {
      logger.info('Ayrshare posting completed successfully:', {
        postId: postResult.data.id,
        platforms: postResult.platforms,
        totalTime: `${totalTime}ms`
      });

      // Emit success update
      io.emit('ayrshare_progress', {
        status: 'completed',
        message: 'Content posted successfully to all platforms',
        postId: postResult.data.id,
        platforms: postResult.platforms,
        totalTime,
        timestamp: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Content generated and posted successfully',
        data: {
          postId: postResult.data.id,
          platforms: postResult.platforms,
          content: content.substring(0, 200) + (content.length > 200 ? '...' : ''),
          contentLength: content.length,
          processingTime: totalTime,
          provider: contentResult.provider,
          ayrshareResponse: postResult.data
        }
      });
    } else {
      throw new Error(`Ayrshare posting failed: ${postResult.error}`);
    }

  } catch (error) {
    logger.error('Ayrshare auto-posting failed:', {
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
 * Manual post endpoint for testing
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

export default router;