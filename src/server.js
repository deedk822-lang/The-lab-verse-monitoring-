// IMPORTANT: Import telemetry FIRST (before anything else)
import './telemetry.js';

import express from 'express';
import cors from 'cors';
import { multiProviderGenerateInstrumented } from './providers/instrumentedProvider.js';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    telemetry: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ? 'enabled' : 'disabled',
  });
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

app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
  console.log(`🔍 Health check: http://localhost:${PORT}/health`);
});
