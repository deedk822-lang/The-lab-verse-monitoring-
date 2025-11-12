import { logger } from '../../monitoring/logger.js';

export class CostOptimizer {
  constructor() {
    this.costs = [];
    this.budgets = new Map();
    this.alerts = [];
  }

  /**
   * Track API call cost
   */
  async track(data) {
    const { provider, cost, tokens, timestamp = Date.now() } = data;

    const record = {
      provider,
      cost,
      tokens,
      timestamp,
      date: new Date(timestamp).toISOString()
    };

    this.costs.push(record);

    // Keep only last 10,000 records
    if (this.costs.length > 10000) {
      this.costs = this.costs.slice(-10000);
    }

    // Check budget alerts
    await this.checkBudgetAlerts(provider, cost);

    logger.debug(`💰 Cost tracked: ${provider} = $${cost.toFixed(6)}`);

    return record;
  }

  /**
   * Calculate cost for provider and usage
   */
  calculateCost(provider, usage) {
    const pricing = {
      'openai': { input: 0.03, output: 0.06 },
      'anthropic': { input: 0.015, output: 0.075 },
      'gemini': { input: 0.00125, output: 0.005 },
      'mistral': { input: 0.002, output: 0.006 },
      'groq': { input: 0.0005, output: 0.0008 },
      'deepseek': { input: 0.0001, output: 0.0002 },
      'perplexity': { input: 0.001, output: 0.005 },
      'moonshot': { input: 0.0002, output: 0.0004 },
      'glm': { input: 0.0001, output: 0.0003 }
    };

    const rates = pricing[provider];
    if (!rates) return 0;

    const inputCost = (usage.inputTokens / 1000) * rates.input;
    const outputCost = (usage.outputTokens / 1000) * rates.output;

    return inputCost + outputCost;
  }

  /**
   * Set budget limit
   */
  setBudget(provider, limit, period = 'daily') {
    this.budgets.set(provider, {
      limit,
      period,
      spent: 0,
      lastReset: Date.now()
    });

    logger.info(`💰 Budget set: ${provider} = $${limit}/${period}`);
  }

  /**
   * Check budget alerts
   */
  async checkBudgetAlerts(provider, cost) {
    const budget = this.budgets.get(provider);
    if (!budget) return;

    // Reset if period expired
    const now = Date.now();
    const periodMs = budget.period === 'daily' ? 86400000 : 2592000000; // daily or monthly

    if (now - budget.lastReset > periodMs) {
      budget.spent = 0;
      budget.lastReset = now;
    }

    // Add to spent
    budget.spent += cost;

    // Check thresholds
    const percentage = (budget.spent / budget.limit) * 100;

    if (percentage >= 90 && !this.alerts.includes(`${provider}-90`)) {
      logger.warn(`🚨 ALERT: ${provider} at ${percentage.toFixed(1)}% of budget`);
      this.alerts.push(`${provider}-90`);
    }

    if (percentage >= 100) {
      logger.error(`🚨 CRITICAL: ${provider} exceeded budget! ($${budget.spent.toFixed(2)}/$${budget.limit})`);
      throw new Error(`Budget exceeded for ${provider}`);
    }
  }

  /**
   * Get cost summary
   */
  async getSummary(period = 'day') {
    const now = Date.now();
    const periodMs = {
      'hour': 3600000,
      'day': 86400000,
      'week': 604800000,
      'month': 2592000000
    }[period];

    const recentCosts = this.costs.filter(c => now - c.timestamp < periodMs);

    const byProvider = {};
    let total = 0;

    recentCosts.forEach(record => {
      if (!byProvider[record.provider]) {
        byProvider[record.provider] = {
          cost: 0,
          calls: 0,
          tokens: 0
        };
      }

      byProvider[record.provider].cost += record.cost;
      byProvider[record.provider].calls++;
      byProvider[record.provider].tokens += record.tokens.inputTokens + record.tokens.outputTokens;

      total += record.cost;
    });

    return {
      period,
      total,
      byProvider,
      callCount: recentCosts.length,
      avgCostPerCall: recentCosts.length > 0 ? total / recentCosts.length : 0
    };
  }

  /**
   * Get cost projection
   */
  async getProjection() {
    const hourly = await this.getSummary('hour');
    const daily = await this.getSummary('day');

    return {
      nextHour: hourly.total,
      nextDay: hourly.total * 24,
      nextWeek: daily.total * 7,
      nextMonth: daily.total * 30
    };
  }

  /**
   * Optimize spending recommendations
   */
  async getRecommendations() {
    const summary = await this.getSummary('day');
    const recommendations = [];

    // Analyze each provider
    for (const [provider, stats] of Object.entries(summary.byProvider)) {
      const avgCost = stats.cost / stats.calls;

      // Recommend cheaper alternatives for high-cost providers
      if (avgCost > 0.01 && provider !== 'deepseek') {
        recommendations.push({
          type: 'cost-reduction',
          provider,
          message: `Consider using cheaper alternatives for simple tasks. Current avg: $${avgCost.toFixed(4)}/call`,
          savings: (avgCost - 0.001) * stats.calls
        });
      }

      // Recommend caching for repeated calls
      if (stats.calls > 100) {
        recommendations.push({
          type: 'caching',
          provider,
          message: `Enable caching to reduce costs. Potential savings: $${(stats.cost * 0.3).toFixed(2)}`,
          savings: stats.cost * 0.3
        });
      }
    }

    return recommendations;
  }
}
