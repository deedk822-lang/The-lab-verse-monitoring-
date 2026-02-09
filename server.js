require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const AutoGLM = require('./src/orchestrators/autoglm');
const GLMIntegration = require('./src/integrations/zhipu-glm');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json(),
  ),
  defaultMeta: { service: 'the-lab-verse-monitoring' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
  ],
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  );
}

const app = express();
const port = Number(process.env.PORT) || 3000;

app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

let autoGLM;
let glm;

try {
  glm = new GLMIntegration();
  autoGLM = new AutoGLM();
  logger.info('GLM and AutoGLM initialized successfully');
} catch (error) {
  logger.warn('GLM/AutoGLM initialization skipped', { error: error.message });
}

app.get('/', (_req, res) => {
  res.json({
    message: 'The Lab Verse Monitoring Stack',
    timestamp: new Date().toISOString(),
    services: ['GLM-4.7', 'AutoGLM'],
  });
});

app.get('/api/test/health', async (_req, res) => {
  try {
    const healthChecks = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        express: { status: 'operational' },
        redis: process.env.REDIS_URL ? { status: 'configured' } : { status: 'not configured' },
        database: process.env.DATABASE_URL ? { status: 'configured' } : { status: 'not configured' },
      },
    };

    if (glm) {
      try {
        const glmTest = await glm.generateText('Hello, are you working?', { maxTokens: 10 });
        healthChecks.services.glm = { status: 'operational', response: `${glmTest.slice(0, 20)}...` };
      } catch (error) {
        healthChecks.services.glm = { status: 'error', error: error.message };
      }
    } else {
      healthChecks.services.glm = { status: 'not configured' };
    }

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

    res.json(healthChecks);
  } catch (error) {
    logger.error('Health check failed', error);
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

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
    res.json({ success: true, content, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('GLM generation failed', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/autoglm/security-analysis', async (_req, res) => {
  try {
    if (!autoGLM) {
      return res.status(500).json({ error: 'AutoGLM not configured' });
    }

    const analysis = await autoGLM.autonomousSecurityAnalysis();
    res.json({ success: true, analysis, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('AutoGLM security analysis failed', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

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
    res.json({ success: true, content: secureContent, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('AutoGLM secure content generation failed', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

const server = app.listen(port, () => {
  logger.info(`Server running on port ${port}`);
  logger.info(`Health check available at http://localhost:${port}/api/test/health`);
});

const shutdown = (signal) => {
  logger.info(`${signal} received, shutting down`);
  server.close(() => process.exit(0));
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

module.exports = app;
