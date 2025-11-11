import express from 'express';
import { body, validationResult } from 'express-validator';
import { ContentGenerator } from '../services/ContentGenerator.js';
import { ProviderFactory } from '../services/ProviderFactory.js';
import { getAvailableProviders } from '../config/providers.js';
import { logger } from '../utils/logger.js';
import { cacheMiddleware } from '../middleware/cache.js';

const router = express.Router();
const contentGenerator = new ContentGenerator();

// Validation rules
const contentValidation = [
  body('topic').notEmpty().withMessage('Topic is required').trim().escape(),
  body('audience').notEmpty().withMessage('Audience is required').trim().escape(),
  body('tone').isIn(['professional', 'casual', 'friendly', 'authoritative', 'conversational'])
    .withMessage('Tone must be one of: professional, casual, friendly, authoritative, conversational'),
  body('language').optional().isLength({ min: 2, max: 5 }).withMessage('Language must be 2-5 characters'),
  body('mediaType').isIn(['text', 'image', 'video', 'audio', 'multimodal'])
    .withMessage('Media type must be one of: text, image, video, audio, multimodal'),
  body('provider').optional().isIn(['openai', 'google', 'localai', 'zai'])
    .withMessage('Provider must be one of: openai, google, localai, zai'),
  body('keywords').optional().isArray().withMessage('Keywords must be an array'),
  body('cta').optional().trim().escape(),
  body('aspectRatio').optional().isIn(['1:1', '16:9', '4:3', '9:16'])
    .withMessage('Aspect ratio must be one of: 1:1, 16:9, 4:3, 9:16'),
  body('length').optional().isIn(['short', 'medium', 'long'])
    .withMessage('Length must be one of: short, medium, long')
];

// Generate content endpoint
router.post('/generate', contentValidation, cacheMiddleware, async (req, res) => {
  try {
    // Check validation results
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
      audience,
      tone,
      language = 'en',
      mediaType = 'text',
      provider = 'google',
      keywords = [],
      cta = null,
      aspectRatio = '16:9',
      length = 'medium',
      options = {}
    } = req.body;

    // Emit progress update via WebSocket
    if (req.io) {
      req.io.emit('content_progress', {
        status: 'started',
        message: 'Starting content generation...'
      });
    }

    const result = await contentGenerator.generateContent({
      topic,
      audience,
      tone,
      language,
      mediaType,
      provider,
      keywords,
      cta,
      aspectRatio,
      length
    }, options);

    // Emit completion update
    if (req.io) {
      req.io.emit('content_progress', {
        status: 'completed',
        message: 'Content generation completed',
        resultId: result.id
      });
    }

    res.json({
      success: true,
      data: result
    });

  } catch (error) {
    logger.error('Content generation failed:', error);

    // Emit error update
    if (req.io) {
      req.io.emit('content_progress', {
        status: 'error',
        message: error.message
      });
    }

    res.status(500).json({
      success: false,
      error: 'Content generation failed',
      message: error.message
    });
  }
});

// Get available providers
router.get('/providers', (req, res) => {
  try {
    const providers = getAvailableProviders();
    res.json({
      success: true,
      data: providers
    });
  } catch (error) {
    logger.error('Failed to get providers:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get providers',
      message: error.message
    });
  }
});

// Test provider connection
router.post('/test-provider', async (req, res) => {
  try {
    const { provider } = req.body;

    if (!provider) {
      return res.status(400).json({
        success: false,
        error: 'Provider is required'
      });
    }

    const result = await ProviderFactory.testProvider(provider);
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    logger.error('Provider test failed:', error);
    res.status(500).json({
      success: false,
      error: 'Provider test failed',
      message: error.message
    });
  }
});

// Test all providers
router.get('/test-all-providers', async (req, res) => {
  try {
    const results = await ProviderFactory.testAllProviders();
    res.json({
      success: true,
      data: results
    });
  } catch (error) {
    logger.error('Provider testing failed:', error);
    res.status(500).json({
      success: false,
      error: 'Provider testing failed',
      message: error.message
    });
  }
});

// Get content by ID (from cache)
router.get('/content/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const content = await contentGenerator.getContentById(id);

    if (!content) {
      return res.status(404).json({
        success: false,
        error: 'Content not found'
      });
    }

    res.json({
      success: true,
      data: content
    });
  } catch (error) {
    logger.error('Failed to get content:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get content',
      message: error.message
    });
  }
});

// Analyze existing content
router.post('/analyze', async (req, res) => {
  try {
    const { content, type = 'text', provider = 'google' } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const aiProvider = ProviderFactory.getProvider(provider);
    const analysis = await aiProvider.analyzeContent(content, { type });

    res.json({
      success: true,
      data: analysis
    });
  } catch (error) {
    logger.error('Content analysis failed:', error);
    res.status(500).json({
      success: false,
      error: 'Content analysis failed',
      message: error.message
    });
  }
});

// Generate SEO suggestions
router.post('/seo', async (req, res) => {
  try {
    const { topic, content, provider = 'google' } = req.body;

    if (!topic || !content) {
      return res.status(400).json({
        success: false,
        error: 'Topic and content are required'
      });
    }

    const aiProvider = ProviderFactory.getProvider(provider);
    const seoData = await contentGenerator.generateSEOData(topic, { content }, aiProvider);

    res.json({
      success: true,
      data: seoData
    });
  } catch (error) {
    logger.error('SEO generation failed:', error);
    res.status(500).json({
      success: false,
      error: 'SEO generation failed',
      message: error.message
    });
  }
});

// Generate social media posts
router.post('/social', async (req, res) => {
  try {
    const { topic, content, platforms = ['twitter', 'linkedin'], provider = 'google' } = req.body;

    if (!topic || !content) {
      return res.status(400).json({
        success: false,
        error: 'Topic and content are required'
      });
    }

    const aiProvider = ProviderFactory.getProvider(provider);
    const socialPosts = await contentGenerator.generateSocialPosts(topic, { content }, aiProvider);

    // Filter by requested platforms
    const filteredPosts = {};
    platforms.forEach(platform => {
      if (socialPosts[platform]) {
        filteredPosts[platform] = socialPosts[platform];
      }
    });

    res.json({
      success: true,
      data: filteredPosts
    });
  } catch (error) {
    logger.error('Social posts generation failed:', error);
    res.status(500).json({
      success: false,
      error: 'Social posts generation failed',
      message: error.message
    });
  }
});

export default router;