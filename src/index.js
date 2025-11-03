import './config/env.js';
import { createApp } from './gateway/index.js';
import pino from 'pino';
const logger = pino({ level: 'info' });

const app = createApp();
const server = app.listen(process.env.PORT, () =>
  logger.info(`API on ${process.env.PORT}`)
);

process.on('SIGTERM', () => {
  logger.info('SIGTERM – shutting down');
  server.close(() => process.exit(0));
});
