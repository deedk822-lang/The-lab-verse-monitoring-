const contentGenerator = require('../services/content-generator');
const seoGenerator = require('../services/seo-generator');
const socialGenerator = require('../services/social-generator');
const { validateContentRequest, enhanceRequest, sanitizeInput } = require('../utils/validator');
const logger = require('../utils/logger');
const costTracker = require('../utils/cost-tracker');
const { v4: uuidv4 } = require('uuid');

class ContentController {
  async createContent(req, res) {
    const requestId = uuidv4();
    
    try {
      logger.info(`Content request received: ${requestId}`, { body: req.body });

      // Validate request
      const { error, value } = validateContentRequest(req.body);
      if (error) {
        logger.warn(`Validation error for ${requestId}:`, error.details);
        return res.status(400).json({
          success: false,
          error: 'Validation failed',
          details: error.details.map(d => d.message)
        });
      }

      // Sanitize and enhance
      const sanitized = {
        ...value,
        topic: sanitizeInput(value.topic),
        audience: sanitizeInput(value.audience)
      };
      const enhancedRequest = enhanceRequest(sanitized);

      logger.info(`Processing content request ${requestId}:`, enhancedRequest);

      // Emit progress via Socket.IO if available
      if (req.app.io) {
        req.app.io.emit('progress', { requestId, status: 'started', message: 'Generating content...' });
      }

      // Generate content
      const content = await contentGenerator.generateContent(enhancedRequest);

      if (req.app.io) {
        req.app.io.emit('progress', { requestId, status: 'content_done', message: 'Content generated, creating SEO...' });
      }

      // Generate SEO metadata if requested
      let seo = null;
      if (enhancedRequest.include_seo && content.type === 'text') {
        seo = await seoGenerator.generateSEOMetadata(
          content.content,
          enhancedRequest.keywords,
          enhancedRequest.topic
        );
      }

      if (req.app.io) {
        req.app.io.emit('progress', { requestId, status: 'seo_done', message: 'SEO created, generating social posts...' });
      }

      // Generate social posts if requested
      let social = null;
      if (enhancedRequest.include_social && content.type === 'text') {
        social = await socialGenerator.generateSocialPosts(
          content.content,
          enhancedRequest.topic,
          enhancedRequest.keywords,
          enhancedRequest.cta
        );

        // Also generate email and YouTube script
        social.email = socialGenerator.generateEmailNewsletter(
          content.content,
          enhancedRequest.topic,
          enhancedRequest.cta
        );
        social.youtube = socialGenerator.generateYouTubeScript(
          enhancedRequest.topic,
          content.content
        );
      }

      // Track costs
      costTracker.trackRequest(requestId, content.provider, {
        mediaType: content.type,
        totalCost: content.totalCost,
        usage: content.usage
      });

      if (req.app.io) {
        req.app.io.emit('progress', { requestId, status: 'completed', message: 'All done!' });
      }

      // Build response
      const response = {
        success: true,
        requestId,
        content,
        seo,
        social,
        metadata: {
          topic: enhancedRequest.topic,
          audience: enhancedRequest.audience,
          tone: enhancedRequest.tone,
          language: enhancedRequest.language,
          mediaType: enhancedRequest.media_type,
          provider: content.provider,
          fromCache: content.fromCache || false
        },
        costs: {
          totalCost: content.totalCost,
          breakdown: costTracker.getCost(requestId)
        },
        timestamp: new Date().toISOString()
      };

      logger.info(`Request ${requestId} completed successfully. Cost: $${content.totalCost.toFixed(4)}`);

      return res.status(200).json(response);

    } catch (error) {
      logger.error(`Error processing request ${requestId}:`, error);
      
      if (req.app.io) {
        req.app.io.emit('progress', { requestId, status: 'error', message: error.message });
      }

      return res.status(500).json({
        success: false,
        requestId,
        error: 'Internal server error',
        message: error.message
      });
    }
  }

  async testEndpoint(req, res) {
    try {
      logger.info('Test endpoint called');

      // Return dummy data without calling real APIs
      const response = {
        success: true,
        requestId: uuidv4(),
        content: {
          type: 'text',
          content: '# Test Article\n\nThis is a test article generated without calling real APIs.\n\nIt demonstrates the structure of the response.',
          format: 'markdown',
          research: 'This is mock research data.',
          sources: ['https://example.com'],
          usage: { research: {}, content: { inputTokens: 100, outputTokens: 200 } },
          totalCost: 0,
          provider: 'test'
        },
        seo: {
          title: 'Test Article - Content Creator AI',
          metaDescription: 'This is a test article generated without calling real APIs.',
          keywords: ['test', 'article', 'demo'],
          ogTags: {
            'og:title': 'Test Article',
            'og:description': 'This is a test article.',
            'og:type': 'article'
          },
          readabilityScore: { score: 75, level: 'Fairly Easy' }
        },
        social: {
          twitter: {
            text: 'Check out this test article! #test #demo #ai',
            length: 45
          },
          linkedin: {
            text: 'Test article for demonstration purposes. #ContentCreation #AI',
            length: 62
          }
        },
        metadata: {
          topic: 'test topic',
          mediaType: 'text',
          provider: 'test',
          fromCache: false
        },
        costs: { totalCost: 0, breakdown: {} },
        timestamp: new Date().toISOString()
      };

      return res.status(200).json(response);
    } catch (error) {
      logger.error('Test endpoint error:', error);
      return res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  async getStats(req, res) {
    try {
      const costs = costTracker.getAllCosts();
      const totalCost = costTracker.getTotalCost();

      const stats = {
        totalRequests: Object.keys(costs).length,
        totalCost,
        averageCost: Object.keys(costs).length > 0 ? totalCost / Object.keys(costs).length : 0,
        requestsByProvider: {},
        costsByProvider: {}
      };

      // Calculate stats by provider
      Object.values(costs).forEach(cost => {
        const provider = cost.provider || 'unknown';
        stats.requestsByProvider[provider] = (stats.requestsByProvider[provider] || 0) + 1;
        stats.costsByProvider[provider] = (stats.costsByProvider[provider] || 0) + (cost.totalCost || 0);
      });

      return res.status(200).json({
        success: true,
        stats
      });
    } catch (error) {
      logger.error('Stats endpoint error:', error);
      return res.status(500).json({
        success: false,
        error: error.message
      });
    }
  }

  async healthCheck(req, res) {
    // const googleProvider = require('../services/providers/google');
    // const localaiProvider = require('../services/providers/localai');
    // const zaiProvider = require('../services/providers/zai');
    // const openaiProvider = require('../services/providers/openai');

    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      providers: {
        // google: googleProvider.isEnabled(),
        // localai: localaiProvider.isEnabled(),
        // zai: zaiProvider.isEnabled(),
        // openai: openaiProvider.isEnabled()
      }
    };

    // // Check LocalAI health if enabled
    // if (localaiProvider.isEnabled()) {
    //   health.localai = await localaiProvider.checkHealth();
    // }

    // const hasAnyProvider = Object.values(health.providers).some(enabled => enabled);
    
    // if (!hasAnyProvider) {
    //   health.status = 'warning';
    //   health.message = 'No AI providers are enabled';
    // }

    const statusCode = health.status === 'healthy' ? 200 : 200;
    return res.status(statusCode).json(health);
  }
}

module.exports = new ContentController();
