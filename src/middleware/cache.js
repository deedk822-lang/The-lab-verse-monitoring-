import { connectRedis } from '../utils/redis.js';
import { logger } from '../utils/logger.js';

const CACHE_TTL = parseInt(process.env.CACHE_TTL) || 3600; // 1 hour default

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
    const originalJson = res.json;

    // Override res.json to cache the response
    res.json = function(data) {
      // Cache the response
      redis.setex(cacheKey, CACHE_TTL, JSON.stringify(data))
        .catch(err => logger.error('Cache set failed:', err));

      // Call original json method
      return originalJson.call(this, data);
    };

    next();
  } catch (error) {
    logger.error('Cache middleware error:', error);
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