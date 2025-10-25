const config = require('../config/config');
const logger = require('./logger');

class CostTracker {
  constructor() {
    this.costs = {};
  }

  calculateTokenCost(provider, model, inputTokens, outputTokens) {
    if (!config.costs.trackCosts) return 0;

    const pricing = config.costs.pricing[provider]?.[model];
    if (!pricing) {
      logger.warn(`No pricing info for ${provider}/${model}`);
      return 0;
    }

    const inputCost = (inputTokens / 1000) * (pricing.input || 0);
    const outputCost = (outputTokens / 1000) * (pricing.output || 0);
    
    return inputCost + outputCost;
  }

  calculateMediaCost(provider, mediaType, units) {
    if (!config.costs.trackCosts) return 0;

    const pricing = config.costs.pricing[provider];
    if (!pricing) return 0;

    if (mediaType === 'image') {
      const model = config.providers[provider]?.models?.imagen || 'imagen-3.0';
      return units * (pricing[model]?.perImage || 0);
    } else if (mediaType === 'video') {
      const model = config.providers[provider]?.models?.veo || 'veo-3.1';
      return units * (pricing[model]?.perSecond || 0);
    } else if (mediaType === 'audio') {
      const model = config.providers[provider]?.models?.tts || 'tts-1';
      return units * (pricing[model]?.perChar || 0);
    }

    return 0;
  }

  trackRequest(requestId, provider, details) {
    if (!config.costs.trackCosts) return;

    this.costs[requestId] = {
      provider,
      timestamp: new Date().toISOString(),
      ...details
    };

    logger.info(`Cost tracked for ${requestId}:`, details);
  }

  getCost(requestId) {
    return this.costs[requestId] || null;
  }

  getAllCosts() {
    return this.costs;
  }

  getTotalCost() {
    return Object.values(this.costs).reduce((sum, cost) => {
      return sum + (cost.totalCost || 0);
    }, 0);
  }
}

module.exports = new CostTracker();
