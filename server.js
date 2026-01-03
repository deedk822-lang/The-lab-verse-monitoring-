import express from 'express';
import fetch from 'node-fetch'; // For making API calls to Vercel
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';
import { createMiddleware } from '@vercel/analytics/server';

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

app.use(createMiddleware());

app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    version: process.env.npm_package_version || 'unknown'
  });
});

app.get('/api/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    version: process.env.npm_package_version || 'unknown'
  });
});

app.get('/ready', (req, res) => {
  res.status(200).json({ status: 'ready' });
});

app.get('/live', (req, res) => {
  res.status(200).json({ status: 'alive' });
});

app.head('/health', (req, res) => {
  res.status(200).end();
});

app.head('/api/health', (req, res) => {
  res.status(200).end();
});

// Middleware for Zero-Trust authentication on the metrics endpoint
const authMetrics = (req, res, next) => {
  const authHeader = req.headers.authorization;
  const token = authHeader && authHeader.split(' ')[1]; // Expects "Bearer TOKEN"

  if (token == null || token !== process.env.METRICS_API_TOKEN) {
    return res.status(401).json({ error: 'Unauthorized: Missing or invalid token.' });
  }
  next();
};

// Real-Time, Secure Metrics API Endpoint with Fallback
app.get('/api/metrics', authMetrics, async (req, res) => {
  try {
    const vercelToken = process.env.VERCEL_TOKEN;
    if (!vercelToken) {
      throw new Error('VERCEL_TOKEN is not configured on the server.');
    }

    const vercelRes = await fetch("https://api.vercel.com/v1/analytics", {
      headers: { Authorization: `Bearer ${vercelToken}` }
    });

    if (!vercelRes.ok) {
      const errorBody = await vercelRes.text();
      console.error(`Vercel API Error: ${vercelRes.status} ${errorBody}`);
      throw new Error('Failed to fetch from Vercel API.');
    }

    const vercelData = await vercelRes.json();

    return res.json({
      requests: vercelData.totalRequests || 0,
      errors: vercelData.errors || 0,
      latency: vercelData.avgLatency || "N/A",
      status: "Healthy",
      source: "Live Vercel Analytics"
    });
  } catch (error) {
    console.error('Metrics API Error:', error.message);
    return res.status(503).json({
      status: 'Degraded',
      source: 'Fallback',
      message: 'Could not retrieve live Vercel Analytics data.'
    });
  }
});

app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    status: 'error',
    message: process.env.NODE_ENV === 'production' ? 'Internal server error' : err.message
  });
});

process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

const server = app.listen(port, () => {
  console.log(`✅ Server running on port ${port}`);
  console.log(`✅ Health check available at http://localhost:${port}/health`);
});

export default app;
