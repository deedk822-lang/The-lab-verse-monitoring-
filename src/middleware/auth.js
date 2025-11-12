import { logger } from '../utils/logger.js';

export const validateApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'] || req.headers['authorization']?.replace('Bearer ', '');
  const expectedApiKey = process.env.API_KEY;

  if (!expectedApiKey) {
    logger.warn('API_KEY not configured, skipping authentication');
    return next();
  }

  if (!apiKey) {
    return res.status(401).json({
      success: false,
      error: 'API key required',
      message: 'Please provide an API key in the x-api-key header or Authorization header'
    });
  }

  if (apiKey !== expectedApiKey) {
    logger.warn(`Invalid API key attempt from ${req.ip}`);
    return res.status(401).json({
      success: false,
      error: 'Invalid API key',
      message: 'The provided API key is invalid'
    });
  }

  logger.info(`Authenticated request from ${req.ip}`);
  next();
};

export const validateWebhookSecret = (req, res, next) => {
  const webhookSecret = req.headers['x-webhook-secret'];
  const expectedSecret = process.env.WEBHOOK_SECRET;

  if (!expectedSecret) {
    logger.warn('WEBHOOK_SECRET not configured, skipping webhook validation');
    return next();
  }

  if (!webhookSecret) {
    return res.status(401).json({
      success: false,
      error: 'Webhook secret required',
      message: 'Please provide a webhook secret in the x-webhook-secret header'
    });
  }

  if (webhookSecret !== expectedSecret) {
    logger.warn(`Invalid webhook secret attempt from ${req.ip}`);
    return res.status(401).json({
      success: false,
      error: 'Invalid webhook secret',
      message: 'The provided webhook secret is invalid'
    });
  }

  next();
};
