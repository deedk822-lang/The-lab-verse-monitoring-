// IMPORTANT: Import telemetry FIRST (before anything else)
import './telemetry.js';

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { multiProviderGenerateInstrumented } from './providers/instrumentedProvider.js';

// Monitoring imports
import { initializeSentry, sentryErrorHandler } from './monitoring/sentry.js';
import { logger, requestLogger } from './monitoring/logger.js';
import { configureSecurityHeaders, configureRateLimiting, configureCORS, suspiciousActivityDetector } from './monitoring/security.js';
import { initializeSpeedInsights } from './monitoring/speedInsights.js';
import { initializeRUM } from './monitoring/rum.js';
import { costTracker, checkCostAlerts, formatCost } from './monitoring/costTracking.js';
import { syntheticMonitor } from './monitoring/synthetic.js';
import monitoringRoutes from './routes/monitoring.js';
import { performanceMiddleware } from './monitoring/performance.js';


// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Initialize Sentry (must be first)
initializeSentry(app);

// Security middleware
configureSecurityHeaders(app);
configureRateLimiting(app);
configureCORS(app);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging
app.use(requestLogger);

// Suspicious activity detection
app.use(suspiciousActivityDetector);

// Performance tracking middleware
app.use(performanceMiddleware);

// Initialize monitoring services
initializeSpeedInsights();
initializeRUM();

// Monitoring routes
app.use('/api/monitoring', monitoringRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    synthetic: syntheticMonitor.getStatus(),
    costs: costTracker.getCostSummary()
  };

  res.json(health);
});

// Research endpoint with OpenTelemetry instrumentation
app.post('/api/research', async (req, res) => {
  try {
    const { q } = req.body;

    if (!q) {
      return res.status(400).json({ error: 'Query parameter "q" is required' });
    }

    const messages = [
      { role: 'user', content: q }
    ];

    const result = await multiProviderGenerateInstrumented({ messages });

    res.json({
      provider: result.provider,
      text: result.text,
      tokens: result.tokens,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('❌ Error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message,
    });
  }
});

// Generate endpoint (alternative)
app.post('/api/generate', async (req, res) => {
  try {
    const { messages, model } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Messages array is required' });
    }

    const result = await multiProviderGenerateInstrumented({ messages, model });

    res.json({
      provider: result.provider,
      text: result.text,
      tokens: result.tokens,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('❌ Error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message,
    });
  }
});

// 404 handler
app.use((req, res) => {
  logger.warn('Route not found', { path: req.path, method: req.method });
  res.status(404).json({ error: 'Not found' });
});

// Sentry error handler (must be before other error handlers)
sentryErrorHandler(app);

// Global error handler
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);

  res.status(err.status || 500).json({
    error: process.env.NODE_ENV === 'production'
      ? 'Internal server error'
      : err.message
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');

  syntheticMonitor.stop();

  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });

  // Force shutdown after 30 seconds
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000);
});

// Start server
const server = app.listen(PORT, () => {
  logger.info(`🚀 Server running on port ${PORT}`);
  logger.info(`📊 Monitoring enabled: Sentry, OpenTelemetry, Cost Tracking, Synthetic`);
  logger.info(`🔒 Security: Rate limiting, CORS, Helmet`);
});

export default app;
