const redis = require('redis');
const logger = require('./logger');
const config = require('../config/config');

let client = null;
let isConnected = false;

async function initRedis() {
  if (!config.redis.enabled) {
    logger.info('Redis caching disabled');
    return false;
  }

  try {
    client = redis.createClient({
      url: config.redis.url
    });

    client.on('error', (err) => {
      logger.error('Redis client error:', err);
      isConnected = false;
    });

    client.on('connect', () => {
      logger.info('Redis client connected');
      isConnected = true;
    });

    await client.connect();
    return true;
  } catch (error) {
    logger.error('Failed to initialize Redis:', error);
    isConnected = false;
    return false;
  }
}

async function get(key) {
  if (!isConnected || !client) return null;

  try {
    const value = await client.get(key);
    return value ? JSON.parse(value) : null;
  } catch (error) {
    logger.error('Redis GET error:', error);
    return null;
  }
}

async function set(key, value, ttl = config.redis.ttl) {
  if (!isConnected || !client) return false;

  try {
    await client.setEx(key, ttl, JSON.stringify(value));
    return true;
  } catch (error) {
    logger.error('Redis SET error:', error);
    return false;
  }
}

async function del(key) {
  if (!isConnected || !client) return false;

  try {
    await client.del(key);
    return true;
  } catch (error) {
    logger.error('Redis DEL error:', error);
    return false;
  }
}

function generateCacheKey(provider, type, params) {
  const paramStr = JSON.stringify(params);
  return `content:${provider}:${type}:${Buffer.from(paramStr).toString('base64')}`;
}

module.exports = {
  initRedis,
  get,
  set,
  del,
  generateCacheKey
};
