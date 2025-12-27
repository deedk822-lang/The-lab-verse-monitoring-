import express from 'express';
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';

// 添加错误处理和基础中间件
import { createMiddleware } from '@vercel/analytics/server';

const app = express();
const port = process.env.PORT || 3000;

// JSON 解析
app.use(express.json());

// 请求日志
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

// Vercel Analytics（可选）
app.use(createMiddleware());

// API 路由
app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

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