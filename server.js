import express from 'express';
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';
 jules-audit-fixes-18339105614089813100

// Disabled: Vercel Speed Insights (@vercel/speed-insights)
// This package is designed for browser-side Web Vitals tracking.
// For server-side performance monitoring, consider:
// - @vercel/analytics (for APM)
// - prom-client (for Prometheus metrics)
// - Custom middleware (for request timing)
// import { initializeSpeedInsights, speedInsightsMiddleware } from './lib/speed-insights.js';
// import metricsHandler from './pages/api/metrics.js';
 main

// 添加错误处理和基础中间件
import { createMiddleware } from '@vercel/analytics/server';

 jules-audit-fixes-18339105614089813100
const app = express();
const port = process.env.PORT || 3000;

// Initialize Vercel Speed Insights for performance tracking
// initializeSpeedInsights();
 main

// JSON 解析
app.use(express.json());

 jules-audit-fixes-18339105614089813100
// 请求日志
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

// Vercel Analytics（可选）
app.use(createMiddleware());

// Add Speed Insights middleware for request performance tracking
// app.use(speedInsightsMiddleware);
 main

// API 路由
app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

 jules-audit-fixes-18339105614089813100
// Enhanced health check endpoints
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

// Additional readiness check (for container orchestration)
app.get('/ready', (req, res) => {
  // Add any service dependencies checks here
  res.status(200).json({ status: 'ready' });
});

// Additional liveness check (for container orchestration)
app.get('/live', (req, res) => {
  // Add any service health checks here
  res.status(200).json({ status: 'alive' });
});

// Support HEAD method for health endpoints as a best practice
app.head('/health', (req, res) => {
  res.status(200).end();
});

app.head('/api/health', (req, res) => {
  res.status(200).end();
});

// app.get('/api/metrics', metricsHandler);
 main

// 错误处理
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Global error handling
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    status: 'error',
    message: process.env.NODE_ENV === 'production' ? 'Internal server error' : err.message
  });
});

// Graceful shutdown handling
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

// Start server
const server = app.listen(port, () => {
  console.log(`✅ Server running on port ${port}`);
  console.log(`✅ Health check available at http://localhost:${port}/health`);
});

export default app;