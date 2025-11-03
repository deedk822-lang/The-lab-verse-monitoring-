// src/utils/priceLock.js
import fs from 'fs';
import path from 'path';

/**
 * Price Lock Utility - Monitors and controls API costs
 */
class PriceLock {
  constructor() {
    this.baselinePath = path.join(process.cwd(), 'config/price-baseline.json');
    this.baseline = this.loadBaseline();
  }

  /**
   * Load price baseline configuration
   */
  loadBaseline() {
    try {
      const data = fs.readFileSync(this.baselinePath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      console.warn('⚠️ Could not load price baseline:', error.message);
      return {
        baseline: {
          providers: {},
          softLimits: { monthlyTotal: 100, dailyTokens: 50000, perRequestTokens: 2000 },
          alertThresholds: { daily: 0.8, monthly: 0.9, perRequest: 0.95 }
        }
      };
    }
  }

  /**
   * Get cost summary
   */
  getCostSummary() {
    const providers = this.baseline.baseline?.providers || {};
    const limits = this.baseline.baseline?.softLimits || {};
    
    return {
      providerCount: Object.keys(providers).length,
      monthlyBudget: limits.monthlyTotal || 100,
      dailyTokenLimit: limits.dailyTokens || 50000,
      providers: Object.entries(providers).map(([key, config]) => ({
        name: config.name || key,
        costPer1M: config.costPer1M || 0,
        maxDailyTokens: config.maxDailyTokens || 0
      }))
    };
  }

  /**
   * Validate provider cost against baseline
   * @param {string} provider - Provider name
   * @param {number} costPer1M - Cost per 1M tokens
   * @param {boolean} strict - Whether to throw on violation
   */
  validateProviderCost(provider, costPer1M, strict = false) {
    const baseline = this.baseline.baseline?.providers?.[provider];
    
    if (!baseline) {
      const msg = `Provider ${provider} not found in baseline`;
      if (strict) throw new Error(msg);
      console.warn('⚠️', msg);
      return false;
    }

    const baselineCost = baseline.costPer1M || 0;
    const increase = costPer1M - baselineCost;
    const percentIncrease = baselineCost > 0 ? (increase / baselineCost) * 100 : 0;
    
    if (increase > 0) {
      const msg = `Cost increase detected for ${provider}: $${baselineCost} → $${costPer1M} (+${percentIncrease.toFixed(1)}%)`;
      if (strict) throw new Error(msg);
      console.warn('⚠️', msg);
      return false;
    }
    
    console.log(`✅ ${provider} cost within baseline: $${costPer1M} (baseline: $${baselineCost})`);
    return true;
  }

  /**
   * Check if daily token limit would be exceeded
   * @param {number} tokensUsed - Tokens used today
   */
  checkDailyTokens(tokensUsed) {
    const limit = this.baseline.baseline?.softLimits?.dailyTokens || 50000;
    const threshold = this.baseline.baseline?.alertThresholds?.daily || 0.8;
    
    const usage = tokensUsed / limit;
    
    if (usage >= 1.0) {
      throw new Error(`Daily token limit exceeded: ${tokensUsed}/${limit} tokens`);
    }
    
    if (usage >= threshold) {
      console.warn(`⚠️ Daily token usage high: ${(usage * 100).toFixed(1)}% (${tokensUsed}/${limit})`);
    }
    
    return usage;
  }

  /**
   * Estimate monthly cost based on current usage
   * @param {Object} usage - Usage statistics
   */
  estimateMonthlyCost(usage = {}) {
    const providers = this.baseline.baseline?.providers || {};
    let totalCost = 0;
    
    Object.entries(providers).forEach(([key, config]) => {
      const tokens = usage[key] || 0;
      const cost = (tokens / 1000000) * (config.costPer1M || 0);
      totalCost += cost;
    });
    
    return {
      estimatedCost: totalCost,
      monthlyLimit: this.baseline.baseline?.softLimits?.monthlyTotal || 100,
      withinBudget: totalCost <= (this.baseline.baseline?.softLimits?.monthlyTotal || 100)
    };
  }
}

// Export singleton instance
const priceLock = new PriceLock();

export default priceLock;

// CommonJS compatibility for require()
module.exports = priceLock;
module.exports.default = priceLock;