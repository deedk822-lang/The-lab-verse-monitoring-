import { App } from './app';
import { logger } from './lib/logger/Logger';

let app: App;

async function main(): Promise<void> {
  app = new App();

  try {
    await app.start();
  } catch (error) {
    logger.error('Failed to start application', { error });
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down gracefully...');
  if (app) {
    await app.stop();
  }
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Shutting down gracefully...');
  if (app) {
    await app.stop();
  }
  process.exit(0);
});

main();