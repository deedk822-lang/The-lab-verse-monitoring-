import express from 'express';
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';
import { requestLogger, logger } from './src/monitoring/logger.js';
import { createMiddleware } from '@vercel/analytics/server';
import { sql } from '@vercel/postgres';

const app = express();
const port = process.env.PORT || 3000;

// JSON parser middleware
app.use(express.json());

// Structured request logging
app.use(requestLogger);

// Vercel Analytics (optional)
app.use(createMiddleware());

// API Routes
app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

// Health check
app.get('/health', async (req, res) => {
  try {
    await sql`SELECT 1`;
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(503).json({ status: 'error', error: 'Database connection failed' });
  }
});

// Error handling
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', { message: err.message, stack: err.stack });
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV !== 'production' ? err.message : undefined,
    stack: process.env.NODE_ENV !== 'production' ? err.stack : undefined
  });
});

// Vercel compatibility
export default app;
