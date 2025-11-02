// src/server.js - FIXED VERSION
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

// Load environment variables
dotenv.config();

const app = express();
const httpServer = createServer(app);

export const io = new Server(httpServer, {
cors: {
origin: process.env.CORS_ORIGIN || '*',
methods: ['GET', 'POST']
}
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// CRITICAL: Mount routes BEFORE other endpoints
app.use('/api/ayrshare', ayrshareRoutes);

// Root endpoint
app.get('/', (req, res) => {
res.json({
name: 'Lab Verse Monitoring - AI Content Distribution',
version: '1.0.0',
status: 'running',
endpoints: {
health: '/health',
zapierWebhook: '/api/ayrshare/ayr',
testWorkflow: '/api/ayrshare/test/workflow',
testAyrshare: '/api/ayrshare/test',
testMailchimp: '/api/ayrshare/test/mailchimp',
contentGeneration: '/catch',
streaming: '/stream'
},
documentation: 'https://github.com/deedk822-lang/The-lab-verse-monitoring-'
});
});

// Health check endpoint
app.get('/health', async (req, res) => {
const provider = getActiveProvider();
res.json({
status: 'healthy',
provider: provider ? 'mistral-local' : 'none',
endpoints: [
'/health',
'/api/ayrshare/ayr',
'/api/ayrshare/test',
'/api/ayrshare/test/workflow'
],
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
logger.error('Content generation failed:', error);
res.status(500).json({ error: error.message });
}
});

// Streaming endpoint
app.post('/stream', async (req, res) => {
res.setHeader('Content-Type', 'text/event-stream');
res.setHeader('Cache-Control', 'no-cache');
res.setHeader('Connection', 'keep-alive');

try {
for await (const chunk of streamContent(req.body.prompt)) {
res.write(`data: ${JSON.stringify({ chunk })}\n\n`);
}
res.write('data: [DONE]\n\n');
res.end();
} catch (error) {
res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
res.end();
}
});

// Socket.io connection handling
io.on('connection', (socket) => {
logger.info('WebSocket client connected:', socket.id);

socket.on('disconnect', () => {
logger.info('WebSocket client disconnected:', socket.id);
});

socket.on('error', (error) => {
logger.error('WebSocket error:', error);
});
});

// 404 handler
app.use((req, res) => {
logger.warn('404 Not Found:', req.path);
res.status(404).json({
error: 'Not Found',
path: req.path,
availableEndpoints: [
'GET /',
'GET /health',
'POST /api/ayrshare/ayr',
'GET /api/ayrshare/test',
'GET /api/ayrshare/test/workflow',
'GET /api/ayrshare/test/mailchimp',
'POST /catch',
'POST /stream'
]
});
});

// Error handler
app.use((err, req, res, next) => {
logger.error('Server error:', {
error: err.message,
stack: err.stack,
path: req.path
});

res.status(err.status || 500).json({
error: 'Internal Server Error',
message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong',
timestamp: new Date().toISOString()
});
});

const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';

httpServer.listen(PORT, HOST, () => {
logger.info(`🚀 Server running on ${HOST}:${PORT}`);
logger.info(`📡 Health check: http://localhost:${PORT}/health`);
logger.info(`🔗 Zapier webhook: http://localhost:${PORT}/api/ayrshare/ayr`);
logger.info(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
logger.info('SIGTERM received, closing server gracefully');
httpServer.close(() => {
logger.info('Server closed');
process.exit(0);
});
});

export default app;