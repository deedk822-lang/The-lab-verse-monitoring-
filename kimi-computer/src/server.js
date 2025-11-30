// src/server.js
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import winston from 'winston';
import { generateContent, streamContent } from './services/contentGenerator.js';
import { getActiveProvider } from './config/providers.js';

const app = express();
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({ format: winston.format.simple() })
  ]
});

app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Health check endpoint
app.get('/health', async (req, res) => {
  const provider = getActiveProvider();
  res.json({
    status: provider ? 'healthy' : 'degraded',
    provider: provider ? 'mistral-local' : 'none',
    timestamp: new Date().toISOString()
  });
});

// Standard generation (Make.com webhook)
app.post('/catch', async (req, res) => {
  try {
    const content = await generateContent(req.body.prompt);
    res.json({
      content,
      provider: 'mistral-local',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Streaming endpoint (optional - for real-time UI)
app.post('/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');

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

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`🚀 Server running on port ${PORT}`);
});

export default app;
