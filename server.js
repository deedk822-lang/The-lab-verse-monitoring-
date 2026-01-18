require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const AutoGLM = require('./src/orchestrators/autoglm');
const GLMIntegration = require('./src/integrations/zhipu-glm');

// Initialize logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.json()
  ),
  defaultMeta: { service: 'the-lab-verse-monitoring' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'static')));

// Initialize GLM and AutoGLM
let autoGLM;
let glm;

try {
  glm = new GLMIntegration();
  autoGLM = new AutoGLM();
  logger.info('GLM and AutoGLM initialized successfully');
} catch (error) {
  logger.error('Failed to initialize GLM/AutoGLM:', error.message);
  // Continue without GLM if not configured
}

// Routes
app.get('/', (req, res) => {
  res.json({
    message: 'The Lab Verse Monitoring Stack with GLM-4.7 and AutoGLM Integration',
    timestamp: new Date().toISOString(),
    services: ['GLM-4.7', 'AutoGLM', 'Alibaba Cloud Access Analyzer']
  });
});

// Health check endpoint - this matches the URL you specified
app.get('/api/test/health', async (req, res) => {
  try {
    const healthChecks = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {}
    };

    // Test GLM connection if configured
    if (glm) {
      try {
        const glmTest = await glm.generateText('Hello, are you working?', { maxTokens: 10 });
        healthChecks.services.glm = { status: 'operational', response: glmTest.substring(0, 20) + '...' };
      } catch (error) {
        healthChecks.services.glm = { status: 'error', error: error.message };
      }
    } else {
      healthChecks.services.glm = { status: 'not configured' };
    }

    // Test AutoGLM functionality if configured
    if (autoGLM) {
      try {
        const findings = await autoGLM.getAlibabaSecurityFindings();
        healthChecks.services.autoglm = { status: 'operational', findingsCount: findings.length };
      } catch (error) {
        healthChecks.services.autoglm = { status: 'error', error: error.message };
      }
    } else {
      healthChecks.services.autoglm = { status: 'not configured' };
    }

    // Test other services
    healthChecks.services.express = { status: 'operational' };
    healthChecks.services.redis = process.env.REDIS_URL ? { status: 'configured' } : { status: 'not configured' };

    // Test database connection if configured
    if (process.env.DATABASE_URL) {
      healthChecks.services.database = { status: 'configured' };
    } else {
      healthChecks.services.database = { status: 'not configured' };
    }

    res.json(healthChecks);
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// GLM content generation endpoint
app.post('/api/glm/generate', async (req, res) => {
  try {
    if (!glm) {
      return res.status(500).json({ error: 'GLM not configured' });
    }

    const { type, context, options } = req.body;

    if (!type || !context) {
      return res.status(400).json({ error: 'Type and context are required' });
    }

    const content = await glm.generateStructuredContent(type, context, options);

    res.json({
      success: true,
      content,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('GLM generation failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// AutoGLM autonomous security analysis endpoint
app.post('/api/autoglm/security-analysis', async (req, res) => {
  try {
    if (!autoGLM) {
      return res.status(500).json({ error: 'AutoGLM not configured' });
    }

    const analysis = await autoGLM.autonomousSecurityAnalysis();

    res.json({
      success: true,
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('AutoGLM security analysis failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// AutoGLM secure content generation endpoint
app.post('/api/autoglm/secure-content', async (req, res) => {
  try {
    if (!autoGLM) {
      return res.status(500).json({ error: 'AutoGLM not configured' });
    }

    const { type, context } = req.body;

    if (!type || !context) {
      return res.status(400).json({ error: 'Type and context are required' });
    }

    const secureContent = await autoGLM.generateSecureContent(type, context);

    res.json({
      success: true,
      content: secureContent,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('AutoGLM secure content generation failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Existing routes from the repository
app.post('/api/ayrshare/ayr', async (req, res) => {
  try {
    const { content, platforms } = req.body;

    if (!content) {
      return res.status(400).json({ error: 'Content is required' });
    }

    // Mock implementation - in real app this would call Ayrshare API
    const mockResponse = {
      success: true,
      platforms: platforms || ['twitter', 'facebook', 'linkedin'],
      scheduled: new Date().toISOString(),
      content: content.substring(0, 100) + '...'
    };

    res.json(mockResponse);
  } catch (error) {
    logger.error('Ayrshare posting failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/elevenlabs/tts', async (req, res) => {
  try {
    const { text, voiceId } = req.body;

    if (!text) {
      return res.status(400).json({ error: 'Text is required' });
    }

    // Mock implementation - in real app this would call ElevenLabs API
    const mockResponse = {
      success: true,
      audioUrl: 'https://example.com/mock-audio.mp3',
      duration: '2.5s',
      voice: voiceId || 'default'
    };

    res.json(mockResponse);
  } catch (error) {
    logger.error('ElevenLabs TTS failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/perplexity/search', async (req, res) => {
  try {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    // Mock implementation - in real app this would call Perplexity API
    const mockResponse = {
      success: true,
      query: query,
      results: [
        { title: 'Sample Result 1', url: 'https://example.com/1', snippet: 'This is a sample result' },
        { title: 'Sample Result 2', url: 'https://example.com/2', snippet: 'Another sample result' }
      ],
      sources: 2
    };

    res.json(mockResponse);
  } catch (error) {
    logger.error('Perplexity search failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Start server
app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
  logger.info(`Health check available at http://localhost:${PORT}/api/test/health`);

  if (glm && autoGLM) {
    logger.info(`GLM-4.7 and AutoGLM integration active`);
  } else {
    logger.info(`GLM-4.7 and AutoGLM not configured (set ZAI_API_KEY to enable)`);
  }
});

module.exports = app;
