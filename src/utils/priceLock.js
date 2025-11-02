import baseline from '../../config/price-baseline.json' assert { type: 'json' };
import { logger } from './logger.js';

/**
 * Price lock utility to enforce cost ceilings
 * Prevents API cost overruns by checking against baseline pricing
 */
class PriceLockManager {
  constructor() {
    this.baseline = baseline.baseline;
    this.enforceMode = process.env.PRICE_LOCK_ENFORCE !== 'false';
    
    if (!this.enforceMode) {
      logger.warn('Price lock enforcement disabled - costs not protected');
    }
  }

  /**
   * Get maximum cost per 1M tokens for a provider
   * @param {string} provider - Provider name
   * @returns {number} - Maximum cost ceiling
   */
  maxCostPer1M(provider) {
    const ceiling = this.baseline.providers[provider]?.costPer1M;
    if (ceiling === undefined) {
      logger.warn(`No price ceiling defined for provider: ${provider}`);
      return Infinity;
    }
    return ceiling;
  }

  /**
   * Get monthly budget limit
   * @returns {number} - Monthly budget in USD
   */
  monthlyBudget() {
    return this.baseline.softLimits.monthlyTotal;
  }

  /**
   * Get daily token limit
   * @returns {number} - Daily token limit
   */
  dailyTokenLimit() {
    return this.baseline.softLimits.dailyTokens;
  }

  /**
   * Validate provider cost against baseline
   * @param {string} provider - Provider name
   * @param {number} quotedCost - Quoted cost per 1M tokens
   * @param {boolean} throwOnViolation - Whether to throw error
   * @returns {boolean} - Whether cost is within limits
   */
  validateProviderCost(provider, quotedCost, throwOnViolation = true) {
    if (!this.enforceMode) {
      return true;
    }

    const ceiling = this.maxCostPer1M(provider);
    const isValid = quotedCost <= ceiling;

    if (!isValid) {
      const message = `Price lock violated: ${provider} quoted ${quotedCost} > ceiling ${ceiling}`;
      logger.error(message);
      
      if (throwOnViolation) {
        throw new Error(message);
      }
    }

    return isValid;
  }

  /**
   * Validate service cost against baseline
   * @param {string} service - Service name
   * @param {number} quotedCost - Quoted cost
   * @param {string} unit - Cost unit (e.g., 'perPost', 'per1000Emails')
   * @returns {boolean} - Whether cost is within limits
   */
  validateServiceCost(service, quotedCost, unit) {
    if (!this.enforceMode) {
      return true;
    }

    const serviceConfig = this.baseline.services[service];
    if (!serviceConfig) {
      logger.warn(`No price ceiling defined for service: ${service}`);
      return true;
    }

    const ceiling = serviceConfig[unit];
    if (ceiling === undefined) {
      logger.warn(`No price ceiling defined for service unit: ${service}.${unit}`);
      return true;
    }

    const isValid = quotedCost <= ceiling;
    if (!isValid) {
      const message = `Service cost violation: ${service} ${unit} quoted ${quotedCost} > ceiling ${ceiling}`;
      logger.error(message);
      throw new Error(message);
    }

    return true;
  }

  /**
   * Get cost summary for monitoring
   * @returns {Object} - Cost summary and limits
   */
  getCostSummary() {
    return {
      baseline: {
        providers: Object.keys(this.baseline.providers).length,
        services: Object.keys(this.baseline.services).length,
        monthlyBudget: this.baseline.softLimits.monthlyTotal,
        dailyTokens: this.baseline.softLimits.dailyTokens
      },
      enforcement: {
        enabled: this.enforceMode,
        generatedAt: baseline.generatedAt,
        version: baseline.metadata.version
      }
    };
  }

  /**
   * Check if spending is within monthly budget
   * @param {number} currentSpend - Current month spending
   * @returns {Object} - Budget status
   */
  checkMonthlyBudget(currentSpend) {
    const budget = this.monthlyBudget();
    const remaining = budget - currentSpend;
    const percentUsed = (currentSpend / budget) * 100;

    return {
      budget,
      currentSpend,
      remaining,
      percentUsed,
      withinLimit: currentSpend <= budget,
      warning: percentUsed > 80,
      critical: percentUsed > 95
    };
  }

  /**
   * Get provider cost comparison
   * @param {string} provider - Provider name
   * @param {number} actualCost - Current actual cost
   * @returns {Object} - Cost comparison
   */
  getProviderCostComparison(provider, actualCost) {
    const ceiling = this.maxCostPer1M(provider);
    const percentOfCeiling = ceiling ? (actualCost / ceiling) * 100 : 0;

    return {
      provider,
      actualCost,
      ceiling,
      percentOfCeiling,
      withinLimit: actualCost <= ceiling,
      savings: ceiling - actualCost
    };
  }
}

// Export singleton instance
const priceLock = new PriceLockManager();
export default priceLock;

// Named exports for convenience
export const { maxCostPer1M, monthlyBudget, dailyTokenLimit, validateProviderCost } = priceLock;