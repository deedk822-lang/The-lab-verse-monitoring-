import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';
import Redis from 'ioredis';
import * as promClient from 'prom-client';
import cluster from 'cluster';
import os from 'os';
import pino from 'pino';

const logger = pino({ level: 'info' });
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

const httpDur = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10],
});
const httpTot = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
});
register.registerMetric(httpDur);
register.registerMetric(httpTot);

const createRateLimiter = (win, max) => rateLimit({
  store: new RedisStore({ sendCommand: (...a) => redis.call(...a) }),
  windowMs: win,
  max,
  standardHeaders: true,
});

async function createApp() {
  const app = express();
  app.use(helmet());
  app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(',') || '*' }));
  app.use(compression());
  app.use(express.json({ limit: '10mb' }));

  app.use((req, res, next) => {
    const start = Date.now();
    res.on('finish', () => {
      const dur = (Date.now() - start) / 1000;
      const route = req.route ? req.route.path : req.path;
      httpDur.labels(req.method, route, res.statusCode).observe(dur);
      httpTot.labels(req.method, route, res.statusCode).inc();
    });
    next();
  });

  app.get('/health', (_, res) => res.json({ status: 'healthy' }));
  app.get('/metrics', (_, res) => res.end(register.metrics()));

  const general = createRateLimiter(15 * 60 * 1000, 1000);
  const strict  = createRateLimiter(15 * 60 * 1000, 100);
  app.use(general);

  const auth = (await import('../middleware/auth.js')).default;
  app.use('/api/video',      strict, auth, (await import('../routes/video.js')).default);
  app.use('/api/text-to-speech', strict, auth, (await import('../routes/tts.js')).default);
  app.use('/api/alerts',     (await import('../routes/alerts.js')).default);

  app.use((err, _req, res, _next) => {
    logger.error(err);
    res.status(500).json({ error: 'Internal Server Error' });
  });
  return app;
}

if (cluster.isPrimary) {
  const cpus = os.cpus().length;
  logger.info(`Master ${process.pid} forking ${cpus}`);
  for (let i = 0; i < cpus; i++) {
    cluster.fork();
  }
  cluster.on('exit', (w) => {
    logger.warn(`Worker ${w.process.pid} died`);
    cluster.fork();
  });
} else {
  const app = createApp();
  app.listen(process.env.PORT, () => logger.info(`Worker ${process.pid} started`));
}

export { createApp, redis };
