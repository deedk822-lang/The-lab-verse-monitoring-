import express from 'express';
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';
import { register } from 'prom-client';

const app = express();
const port = process.env.PORT || 3000;

// JSON parser middleware
app.use(express.json());

// Request logging (基础监控)
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} - ${res.statusCode} (${duration}ms)`);
  });
  next();
});

// Routes
app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

// Metrics endpoint (Prometheus)
app.get('/api/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling (必须在所有路由之后)
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Start server
app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});