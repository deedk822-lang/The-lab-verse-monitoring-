import express from 'express';
import cors from 'cors';
import { logger } from './lib/logger/Logger';
import { config } from './lib/config/Config';
import { metrics } from './lib/metrics/Metrics';
import { register } from 'prom-client';
import routes from './routes';

export class App {
  private app: express.Application;
  private server: any;

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  private setupMiddleware(): void {
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Metrics middleware
    this.app.use((req, res, next) => {
      const start = Date.now();

      res.on('finish', () => {
        const duration = (Date.now() - start) / 1000;
        metrics.httpRequestsTotal.inc({
          method: req.method,
          route: req.route?.path || req.path,
          status_code: res.statusCode
        });
        metrics.httpRequestDuration.observe({
            method: req.method,
            route: req.route?.path || req.path
        }, duration);
      });

      next();
    });
  }

  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date(),
        version: '1.0.0'
      });
    });

    // Metrics endpoint
    this.app.get('/metrics', async (req, res) => {
      res.set('Content-Type', register.contentType);
      res.end(await register.metrics());
    });

    // API routes
    this.app.use('/api/v1', routes);
  }

  private setupErrorHandling(): void {
    this.app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
      logger.error('Unhandled error', { error: err.message, stack: err.stack });
      res.status(500).json({ error: 'Internal server error' });
    });
  }

  async start(): Promise<void> {
    const port = config.get().PORT;

    this.server = this.app.listen(port, () => {
      logger.info(`LapVerse server started on port ${port}`);
    });
  }

  async stop(): Promise<void> {
    if (this.server) {
      return new Promise((resolve) => {
        this.server.close(resolve);
      });
    }
  }
}