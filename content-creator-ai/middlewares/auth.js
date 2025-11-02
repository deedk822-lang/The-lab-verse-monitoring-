const config = require('../config/config');
const logger = require('../utils/logger');

function apiKeyAuth(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.query.api_key;

  if (!apiKey) {
    logger.warn('API request without API key');
    return res.status(401).json({
      success: false,
      error: 'Unauthorized',
      message: 'API key is required. Provide it in X-API-Key header or api_key query parameter.'
    });
  }

  if (apiKey !== config.server.apiKey) {
    logger.warn('API request with invalid API key');
    return res.status(403).json({
      success: false,
      error: 'Forbidden',
      message: 'Invalid API key.'
    });
  }

  next();
}

module.exports = { apiKeyAuth };
