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
// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
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

// Vercel 兼容
export default app;