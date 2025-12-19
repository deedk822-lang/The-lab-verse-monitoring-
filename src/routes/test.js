import express from 'express';
import { ProviderFactory } from '../services/ProviderFactory.js';
import { getAvailableProviders } from '../config/providers.js';
import { logger } from '../utils/logger.js';
import ayrshareService from '../services/ayrshareService.js';

const router = express.Router();

// Test endpoint for basic functionality
router.get('/', (req, res) => {
  res.json({
    success: true,
    message: 'AI Content Creation Suite is running!',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
  });
});

// Test all providers
router.get('/providers', async (req, res) => {
  try {
    const providers = getAvailableProviders();
    const testResults = await ProviderFactory.testAllProviders();

    res.json({
      success: true,
      data: {
        available: providers,
        testResults,
      },
    });
  } catch (error) {
    logger.error('Provider test failed:', error);
    res.status(500).json({
      success: false,
      error: 'Provider test failed',
      message: error.message,
    });
  }
});

// Test specific provider
router.get('/providers/:provider', async (req, res) => {
  try {
    const { provider } = req.params;
    const result = await ProviderFactory.testProvider(provider);

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error(`Provider ${req.params.provider} test failed:`, error);
    res.status(500).json({
      success: false,
      error: `Provider ${req.params.provider} test failed`,
      message: error.message,
    });
  }
});

// Test Ayrshare connection and functionality
router.get('/ayrshare', async (req, res) => {
  try {
    const isConnected = await ayrshareService.testConnection();
    const profile = isConnected ? await ayrshareService.getUserProfile() : null;

    res.json({
      success: isConnected,
      message: isConnected ? 'Ayrshare connection successful' : 'Ayrshare connection failed',
      data: {
        connected: isConnected,
        profile: profile?.data || null,
        apiKeyConfigured: !!process.env.AYRSHARE_API_KEY,
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    logger.error('Ayrshare test failed:', error);
    res.status(500).json({
      success: false,
      error: 'Ayrshare test failed',
      message: error.message,
    });
  }
});

// Test content generation with dummy data
router.post('/generate', async (req, res) => {
  try {
    const { ContentGenerator } = await import('../services/ContentGenerator.js');
    const contentGenerator = new ContentGenerator();

    const testRequest = {
      topic: 'Artificial Intelligence in Content Creation',
      audience: 'marketing professionals',
      tone: 'professional',
      language: 'en',
      mediaType: 'text',
      provider: 'google',
      keywords: ['AI', 'content', 'marketing', 'automation'],
      length: 'medium',
    };

    const result = await contentGenerator.generateContent(testRequest);

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Test content generation failed:', error);
    res.status(500).json({
      success: false,
      error: 'Test content generation failed',
      message: error.message,
    });
  }
});

// Test full Ayrshare workflow (generate + post)
router.post('/ayrshare-workflow', async (req, res) => {
  try {
    const { topic = 'AI Technology Trends', platforms = 'twitter,linkedin' } = req.body;

    // Step 1: Generate content
    const { ContentGenerator } = await import('../services/ContentGenerator.js');
    const contentGenerator = new ContentGenerator();

    const contentRequest = {
      topic,
      audience: 'tech professionals',
      tone: 'professional',
      mediaType: 'text',
      provider: 'google',
      keywords: ['AI', 'technology', 'innovation'],
      length: 'short',
      options: {
        optimizeForSocial: true,
        includeTags: true,
        platforms: platforms.split(',').map(p => p.trim()),
      },
    };

    const contentResult = await contentGenerator.generateContent(contentRequest);

    if (!contentResult.success) {
      throw new Error(`Content generation failed: ${contentResult.error}`);
    }

    // Step 2: Post to Ayrshare (test mode)
    const postResult = await ayrshareService.post({
      post: contentResult.content,
      platforms: platforms,
      options: {
        test: true, // This would be a test mode if Ayrshare supports it
      },
    });

    res.json({
      success: true,
      data: {
        contentGeneration: {
          success: contentResult.success,
          content: contentResult.content.substring(0, 200) + '...',
          provider: contentResult.provider,
          metadata: contentResult.metadata,
        },
        socialPosting: {
          success: postResult.success,
          platforms: postResult.platforms || platforms.split(','),
          postId: postResult.data?.id,
          error: postResult.error,
        },
      },
    });
  } catch (error) {
    logger.error('Ayrshare workflow test failed:', error);
    res.status(500).json({
      success: false,
      error: 'Ayrshare workflow test failed',
      message: error.message,
    });
  }
});

// Test webhook endpoint
router.post('/webhook', (req, res) => {
  const { body, headers } = req;

  logger.info('Webhook test received:', {
    headers: headers,
    body: body,
    timestamp: new Date().toISOString(),
  });

  res.json({
    success: true,
    message: 'Webhook test successful',
    received: {
      headers: Object.keys(headers),
      bodyKeys: Object.keys(body),
      timestamp: new Date().toISOString(),
    },
  });
});

// Health check with detailed status including Ayrshare
router.get('/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      environment: process.env.NODE_ENV || 'development',
      providers: {},
      services: {},
    };

    // Test each AI provider
    const providers = getAvailableProviders();
    for (const provider of providers) {
      try {
        const testResult = await ProviderFactory.testProvider(provider.id);
        health.providers[provider.id] = {
          status: testResult.success ? 'healthy' : 'unhealthy',
          message: testResult.success ? 'OK' : testResult.error,
        };
      } catch (error) {
        health.providers[provider.id] = {
          status: 'unhealthy',
          message: error.message,
        };
      }
    }

    // Test Ayrshare service
    try {
      const ayrshareHealthy = await ayrshareService.testConnection();
      health.services.ayrshare = {
        status: ayrshareHealthy ? 'healthy' : 'unhealthy',
        message: ayrshareHealthy ? 'OK' : 'Connection failed',
        configured: !!process.env.AYRSHARE_API_KEY,
      };
    } catch (error) {
      health.services.ayrshare = {
        status: 'unhealthy',
        message: error.message,
        configured: !!process.env.AYRSHARE_API_KEY,
      };
    }

    const allProvidersHealthy = Object.values(health.providers).every(p => p.status === 'healthy');
    const allServicesHealthy = Object.values(health.services).every(s => s.status === 'healthy');
    health.status = (allProvidersHealthy && allServicesHealthy) ? 'healthy' : 'degraded';

    res.json(health);
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

// Test Redis connection
router.get('/redis', async (req, res) => {
  try {
    const { connectRedis } = await import('../utils/redis.js');
    const redis = await connectRedis();

    // Test basic operations
    await redis.set('test:key', 'test:value', 'EX', 10);
    const value = await redis.get('test:key');
    await redis.del('test:key');

    res.json({
      success: true,
      message: 'Redis connection successful',
      test: value === 'test:value',
    });
  } catch (error) {
    logger.error('Redis test failed:', error);
    res.status(500).json({
      success: false,
      error: 'Redis connection failed',
      message: error.message,
    });
  }
});

// Test file upload
router.post('/upload', (req, res) => {
  // This would test file upload functionality
  res.json({
    success: true,
    message: 'File upload test endpoint ready',
    note: 'Use multipart/form-data with a file field',
  });
});

// Performance test including Ayrshare
router.get('/performance', async (req, res) => {
  const startTime = Date.now();

  try {
    // Test AI providers
    const providers = getAvailableProviders();
    const testPromises = providers.map(provider =>
      ProviderFactory.testProvider(provider.id),
    );

    // Test Ayrshare
    testPromises.push(ayrshareService.testConnection());

    await Promise.all(testPromises);

    const endTime = Date.now();
    const duration = endTime - startTime;

    res.json({
      success: true,
      performance: {
        duration: `${duration}ms`,
        providers: providers.length,
        services: 1, // Ayrshare
        averagePerProvider: `${Math.round(duration / (providers.length + 1))}ms`,
      },
    });
  } catch (error) {
    logger.error('Performance test failed:', error);
    res.status(500).json({
      success: false,
      error: 'Performance test failed',
      message: error.message,
    });
  }
});

export default router;
