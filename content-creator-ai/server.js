require('dotenv').config();
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const bodyParser = require('body-parser');
const path = require('path');

const config = require('./config/config');
const logger = require('./utils/logger');
const cache = require('./utils/cache');
const publicApiRoutes = require('./routes/publicApi');
const apiRoutes = require('./routes/api');
const enhancedKeywordResearchRoutes = require('./routes/enhancedKeywordResearch.js');
const { apiKeyAuth } = require('./middlewares/auth');

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Make io available in routes
app.io = io;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: false // Allow inline scripts for demo UI
}));
app.use(cors());
app.use(compression());

// Body parsing middleware
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: config.rateLimit.windowMs,
  max: config.rateLimit.max,
  message: {
    success: false,
    error: 'Too many requests',
    message: 'Rate limit exceeded. Please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false
});

app.use('/api', limiter);

// Static files
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Routes
app.get('/', (req, res) => {
  res.render('index', { 
    config: {
      providers: Object.keys(config.providers).filter(p => config.providers[p].enabled || p === 'default')
    }
  });
});

// API routes with authentication (except health and test)
app.use('/api', publicApiRoutes);
app.use('/api/keyword-research', enhancedKeywordResearchRoutes);
app.use('/api', apiKeyAuth, apiRoutes);

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);
  
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: config.server.env === 'development' ? err.message : 'An error occurred'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Not found',
    message: 'The requested endpoint does not exist'
  });
});

// Initialize and start server
async function start() {
  try {
    // Initialize Redis cache
    await cache.initRedis();

    // Start server
    const port = config.server.port;
    server.listen(port, () => {
      logger.info('='.repeat(60));
      logger.info(`🚀 Content Creator AI Server Started`);
      logger.info('='.repeat(60));
      logger.info(`Environment: ${config.server.env}`);
      logger.info(`Server running on: http://localhost:${port}`);
      logger.info(`API endpoint: http://localhost:${port}/api/content`);
      logger.info(`Health check: http://localhost:${port}/api/health`);
      logger.info(`Test endpoint: http://localhost:${port}/api/test`);
      logger.info('='.repeat(60));
      logger.info('Enabled AI Providers:');
      Object.entries(config.providers).forEach(([name, prov]) => {
        if (name !== 'default' && prov.enabled) {
          logger.info(`  ✓ ${name}`);
        }
      });
      logger.info('='.repeat(60));
      logger.info('Quick Start:');
      logger.info('1. Copy .env.example to .env and configure your API keys');
      logger.info('2. Open http://localhost:' + port + ' in your browser');
      logger.info('3. Or use the API with X-API-Key header');
      logger.info('='.repeat(60));
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully...');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

// Start the server
start();

module.exports = app;
