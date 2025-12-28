// src/middleware/auth.js - FIXED
import logger from '../utils/logger.js';

export default function authMiddleware(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.headers['authorization']?.replace('Bearer ', '');
  const expectedApiKey = process.env.API_KEY;

  // ✅ CRITICAL FIX: NEVER skip authentication in production
  if (!expectedApiKey) {
    logger.error('❌ SECURITY CRITICAL: API_KEY not configured - rejecting request');
    return res.status(500).json({
      error: 'Server configuration error',
      message: 'Authentication is not properly configured. Contact system administrator.'
    });
  }

  if (!apiKey) {
    logger.warn('Authentication failed: No API key provided', {
      ip: req.ip,
      path: req.path
    });
    return res.status(401).json({
      error: 'Authentication required',
      message: 'Please provide an API key via X-API-Key header or Authorization: Bearer token'
    });
  }

  if (apiKey !== expectedApiKey) {
    logger.warn('Authentication failed: Invalid API key', {
      ip: req.ip,
      path: req.path
    });
    return res.status(403).json({
      error: 'Forbidden',
      message: 'Invalid API key'
    });
  }

  // ✅ Authentication successful
  next();
}
