require('./config/env');
const { createApp } = require('./gateway');
const pino = require('pino');
const logger = pino({ level: 'info' });

const app = createApp();
const server = app.listen(process.env.PORT, () =>
  logger.info(`API on ${process.env.PORT}`)
);

process.on('SIGTERM', () => {
  logger.info('SIGTERM – shutting down');
  server.close(() => process.exit(0));
});