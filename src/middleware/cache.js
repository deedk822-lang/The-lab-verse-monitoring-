import { connectRedis } from '../utils/redis.js';
import { logger } from '../utils/logger.js';
import { Counter } from 'prom-client';

const CACHE_TTL = parseInt(process.env.CACHE_TTL) || 3600; // 1 hour default

// ✅ Prometheus metrics for cache degradation
const cacheFailureCounter = new Counter({
  name: 'cache_failure_total',
  help: 'Total number of cache operation failures',
  labelNames: ['operation']
});

const cacheDegradationCounter = new Counter({
  name: 'cache_degradation_total',
  help: 'Total number of requests served without cache due to failures'
});

export const cacheMiddleware = async (req, res, next) => {
  // Only cache GET requests
  if (req.method !== 'GET') {
    return next();
  }

  try {
    const redis = await connectRedis();
    const cacheKey = `cache:${req.originalUrl}:${JSON.stringify(req.query)}`;

    const cached = await redis.get(cacheKey);
    if (cached) {
      logger.info(`Cache hit for ${cacheKey}`);
      return res.json(JSON.parse(cached));
    }

    // Store original res.json
    const originalJson = res.json.bind(res);

    // Override res.json to cache the response
    res.json = function (data) {
      // Cache the response
      redis.setex(cacheKey, CACHE_TTL, JSON.stringify(data))
        .catch(err => {
            logger.error('Cache set failed:', err);
            cacheFailureCounter.inc({ operation: 'set' });
        });

      // Call original json method
      return originalJson(data);
    };

    next();
  } catch (error) {
    logger.error('❌ Cache middleware error:', error);
    cacheFailureCounter.inc({ operation: 'get' });
    cacheDegradationCounter.inc();

    // This is a simplified way to check the value for alerting, as shown in the guide.
    // In a real-world scenario, you might use a more robust method to get the counter value.
    if (cacheDegradationCounter.collect) {
        const metrics = await cacheDegradationCounter.get();
        const value = metrics.values[0]?.value || 0;
        if (value > 100) {
            logger.error('🚨 ALERT: High cache degradation rate detected - check Redis connection');
        }
    }


    next(); // Continue without caching
  }
};

export const cacheContent = async (key, data, ttl = CACHE_TTL) => {
  try {
    const redis = await connectRedis();
    await redis.setex(`content:${key}`, ttl, JSON.stringify(data));
    logger.info(`Content cached with key: content:${key}`);
  } catch (error) {
    logger.error('Failed to cache content:', error);
  }
};

export const getCachedContent = async (key) => {
  try {
    const redis = await connectRedis();
    const cached = await redis.get(`content:${key}`);
    if (cached) {
      logger.info(`Cache hit for content:${key}`);
      return JSON.parse(cached);
    }
    return null;
  } catch (error) {
    logger.error('Failed to get cached content:', error);
    return null;
  }
};

export const invalidateCache = async (pattern) => {
  try {
    const redis = await connectRedis();
    const keys = await redis.keys(pattern);
    if (keys.length > 0) {
      await redis.del(...keys);
      logger.info(`Invalidated ${keys.length} cache keys matching ${pattern}`);
    }
  } catch (error) {
    logger.error('Failed to invalidate cache:', error);
  }
};
