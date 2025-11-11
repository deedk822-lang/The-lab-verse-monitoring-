import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { createServer } from 'http';
import { Server } from 'socket.io';
import dotenv from 'dotenv';
import { logger } from './utils/logger.js';
import { generateContent, streamContent } from './services/contentGenerator.js';
import { getActiveProvider } from './config/providers.js';
import ayrshareRoutes from './routes/ayrshare.js';

dotenv.config();

const app = express();
const httpServer = createServer(app);

export const io = new Server(httpServer, {
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST']
  }
});

app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Mount routes
app.use('/api/ayrshare', ayrshareRoutes);

// Root endpoint
app.get('/', (_, res) => res.json({ uptime: process.uptime(), repo: 'the-lab-verse-monitoring' }));

// Root endpoint
app.get('/info', (req, res) => {
  res.json({
    name: 'Lab Verse Monitoring - AI Content Distribution',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/health',
      zapierWebhook: '/api/ayrshare/ayr',
      testWorkflow: '/api/ayrshare/test/workflow',
      contentGeneration: '/catch',
      streaming: '/stream'
    }
  });
});

app.get('/health', async (req, res) => {
  const provider = getActiveProvider();
  res.json({
    status: 'healthy',
    provider: provider ? 'available' : 'none',
    timestamp: new Date().toISOString()
  });
});

app.post('/catch', async (req, res) => {
  try {
    if (!req.body.prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    const content = await generateContent(req.body.prompt);
    res.json({
      content,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Content generation failed:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  try {
    for await (const chunk of streamContent(req.body.prompt)) {
      res.write(`data: ${JSON.stringify({ chunk })}\n\n`);
    }
    res.end();
  } catch (error) {
    res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
    res.end();
  }
});

io.on('connection', (socket) => {
  logger.info('WebSocket client connected:', socket.id);
  socket.on('disconnect', () => {
    logger.info('WebSocket client disconnected:', socket.id);
  });
});

app.use((req, res, _next) => {
  res.status(404).json({
    error: 'Not Found',
    path: req.path
  });
});

app.use((err, req, res, _next) => {
  logger.error('Server error:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

const PORT = process.env.PORT || 3000;
httpServer.listen(PORT, '0.0.0.0', () => {
  logger.info(`🚀 Server running on port ${PORT}`);
});

process.on('SIGTERM', () => {
  logger.info('SIGTERM received, closing server');
  httpServer.close(() => process.exit(0));
});

export default app;
