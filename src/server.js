// Import telemetry FIRST
import './telemetry.js';

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

// Monitoring imports
import { initializeSentry, sentryErrorHandler } from './monitoring/sentry.js';
import { logger, requestLogger } from './monitoring/logger.js';
import { configureSecurityHeaders, configureRateLimiting, configureCORS, suspiciousActivityDetector } from './monitoring/security.js';
import { initializeSpeedInsights } from './monitoring/speedInsights.js';
import { initializeRUM } from './monitoring/rum.js';
import { costTracker, checkCostAlerts, formatCost } from './monitoring/costTracking.js';
import { syntheticMonitor } from './monitoring/synthetic.js';

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

// Initialize monitoring services
initializeSpeedInsights();
initializeRUM();

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

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    const metrics = {
      costs: costTracker.getCostSummary(),
      synthetic: syntheticMonitor.getStatus(),
      alerts: checkCostAlerts(costTracker.getCostSummary())
    };

    res.json(metrics);
  } catch (error) {
    logger.error('Error fetching metrics:', error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

// Example API endpoint with cost tracking
app.post('/api/research', async (req, res) => {
  const startTime = Date.now();

  try {
    const { q, provider, model } = req.body;

    if (!q) {
      return res.status(400).json({ error: 'Query parameter required' });
    }

    // Simulate API call
    const result = {
      query: q,
      results: [],
      timestamp: new Date().toISOString()
    };

    // Track costs (example)
    const duration = Date.now() - startTime;
    costTracker.trackCost(provider, model, 100, 200);

    logger.info('Research query processed', { query: q, duration });

    res.json(result);

  } catch (error) {
    logger.error('Research query failed:', error);
    res.status(500).json({ error: 'Internal server error' });
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
