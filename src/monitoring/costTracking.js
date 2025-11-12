import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('cost-tracking', '1.0.0');

// Cost metrics
const costCounter = meter.createCounter('ai_provider_cost_total', {
description: 'Total estimated costs per provider',
unit: 'USD'
});

const tokenCostCounter = meter.createCounter('ai_provider_token_cost', {
description: 'Cost per token by provider',
unit: 'USD'
});

// Pricing data (as of 2025 - update regularly)
const PRICING = {
'OpenAI': {
'gpt-4': { input: 0.00003, output: 0.00006 },
'gpt-4-turbo': { input: 0.00001, output: 0.00003 },
'gpt-3.5-turbo': { input: 0.0000005, output: 0.0000015 }
},
'Anthropic': {
'claude-3-opus': { input: 0.000015, output: 0.000075 },
'claude-3-sonnet': { input: 0.000003, output: 0.000015 },
'claude-3-haiku': { input: 0.00000025, output: 0.00000125 }
},
'Groq': {
'llama-3.1-70b-versatile': { input: 0.0000006, output: 0.0000008 },
'llama-3.1-8b-instant': { input: 0.00000005, output: 0.00000008 }
},
'Gemini': {
'gemini-pro': { input: 0.00000025, output: 0.0000005 },
'gemini-pro-vision': { input: 0.00000025, output: 0.0000005 }
},
'Perplexity': {
'sonar-small-online': { input: 0.0000002, output: 0.0000002 },
'sonar-medium-online': { input: 0.0000006, output: 0.0000006 }
}
};

export class CostTracker {
constructor() {
this.dailyCosts = new Map();
this.monthlyCosts = new Map();
}

/**
* Get total cost
*/
getTotalCost() {
    return Array.from(this.dailyCosts.values()).reduce((a, b) => a + b, 0);
}

/**
* Get cost by service
*/
getCostByService() {
    const byService = {};
    for (const [key, cost] of this.dailyCosts.entries()) {
        const [provider] = key.split(':');
        byService[provider] = (byService[provider] || 0) + cost;
    }
    return byService;
}

/**
* Check for cost alerts
*/
checkAlerts() {
    return checkCostAlerts(this.getCostSummary());
}

/**
* Get cost by period
*/
getCostByPeriod(period = 'day') {
    const byPeriod = {};
    const costs = period === 'day' ? this.dailyCosts : this.monthlyCosts;
    for (const [key, cost] of costs.entries()) {
        const [, date] = key.split(':');
        byPeriod[date] = (byPeriod[date] || 0) + cost;
    }
    return byPeriod;
}

/**
* Get metrics
*/
getMetrics() {
    return {
        total: this.getTotalCost(),
        byService: this.getCostByService(),
        daily: this.getCostByPeriod('day'),
        monthly: this.getCostByPeriod('month')
    };
}

/**
* Project daily cost
*/
projectDailyCost() {
    const now = new Date();
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const secondsElapsed = (now.getTime() - startOfDay.getTime()) / 1000;
    const secondsInDay = 24 * 60 * 60;
    const dailyTotal = this.getCostSummary().total || 0;
    if (secondsElapsed === 0) return 0;
    return (dailyTotal / secondsElapsed) * secondsInDay;
}

/**
* Project monthly cost
*/
projectMonthlyCost() {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const secondsElapsed = (now.getTime() - startOfMonth.getTime()) / 1000;
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const secondsInMonth = daysInMonth * 24 * 60 * 60;
    const monthlyTotal = Object.values(this.getCostSummary().monthly).reduce((a, b) => a + b, 0);
    if (secondsElapsed === 0) return 0;
    return (monthlyTotal / secondsElapsed) * secondsInMonth;
}

/**
* Reset costs
*/
resetCosts() {
    this.dailyCosts.clear();
    this.monthlyCosts.clear();
}

/**
* Track cost for an AI request
*/
trackCost(provider, model, inputTokens, outputTokens) {
const pricing = PRICING[provider]?.[model];

if (!pricing) {
console.warn(`No pricing data for ${provider}/${model}`);
return 0;
}

const inputCost = (inputTokens / 1000) * pricing.input;
const outputCost = (outputTokens / 1000) * pricing.output;
const totalCost = inputCost + outputCost;

// Record metrics
costCounter.add(totalCost, {
provider,
model,
cost_type: 'total'
});

tokenCostCounter.add(inputCost, {
provider,
model,
token_type: 'input'
});

tokenCostCounter.add(outputCost, {
provider,
model,
token_type: 'output'
});

// Track daily costs
const today = new Date().toISOString().split('T')[0];
const dailyKey = `${provider}:${today}`;
this.dailyCosts.set(dailyKey, (this.dailyCosts.get(dailyKey) || 0) + totalCost);

// Track monthly costs
const month = today.substring(0, 7);
const monthlyKey = `${provider}:${month}`;
this.monthlyCosts.set(monthlyKey, (this.monthlyCosts.get(monthlyKey) || 0) + totalCost);

return totalCost;
}

/**
* Get cost summary
*/
getCostSummary() {
const today = new Date().toISOString().split('T')[0];
const month = today.substring(0, 7);

const summary = {
daily: {},
monthly: {},
total: 0
};

// Calculate daily costs
for (const [key, cost] of this.dailyCosts.entries()) {
const [provider, date] = key.split(':');
if (date === today) {
summary.daily[provider] = cost;
summary.total += cost;
}
}

// Calculate monthly costs
for (const [key, cost] of this.monthlyCosts.entries()) {
const [provider, m] = key.split(':');
if (m === month) {
summary.monthly[provider] = cost;
}
}

return summary;
}

/**
* Get cost by provider
*/
getCostByProvider(provider, period = 'daily') {
const date = period === 'daily'
? new Date().toISOString().split('T')[0]
: new Date().toISOString().substring(0, 7);

const key = `${provider}:${date}`;
const costs = period === 'daily' ? this.dailyCosts : this.monthlyCosts;

return costs.get(key) || 0;
}

/**
* Estimate cost before making request
*/
estimateCost(provider, model, estimatedTokens) {
const pricing = PRICING[provider]?.[model];

if (!pricing) {
return 0;
}

// Assume 60/40 split between input/output
const inputTokens = estimatedTokens * 0.6;
const outputTokens = estimatedTokens * 0.4;

return ((inputTokens / 1000) * pricing.input) + ((outputTokens / 1000) * pricing.output);
}

/**
* Get cheapest provider for estimated tokens
*/
getCheapestProvider(estimatedTokens) {
let cheapest = null;
let lowestCost = Infinity;

for (const [provider, models] of Object.entries(PRICING)) {
for (const [model, pricing] of Object.entries(models)) {
const cost = this.estimateCost(provider, model, estimatedTokens);

if (cost < lowestCost) {
lowestCost = cost;
cheapest = { provider, model, cost };
}
}
}

return cheapest;
}
}

// Export singleton instance
export const costTracker = new CostTracker();

// Helper function to format cost
export function formatCost(cost) {
return `$${cost.toFixed(6)}`;
}

// Cost alert thresholds
export const COST_ALERTS = {
daily: {
warning: 10.00, // $10/day
critical: 50.00 // $50/day
},
monthly: {
warning: 200.00, // $200/month
critical: 1000.00 // $1000/month
}
};

// Check if costs exceed thresholds
export function checkCostAlerts(summary) {
const alerts = [];

// Check daily costs
const dailyTotal = Object.values(summary.daily).reduce((a, b) => a + b, 0);
if (dailyTotal >= COST_ALERTS.daily.critical) {
alerts.push({
level: 'critical',
message: `Daily cost ${formatCost(dailyTotal)} exceeds critical threshold ${formatCost(COST_ALERTS.daily.critical)}`
});
} else if (dailyTotal >= COST_ALERTS.daily.warning) {
alerts.push({
level: 'warning',
message: `Daily cost ${formatCost(dailyTotal)} exceeds warning threshold ${formatCost(COST_ALERTS.daily.warning)}`
});
}

// Check monthly costs
const monthlyTotal = Object.values(summary.monthly).reduce((a, b) => a + b, 0);
if (monthlyTotal >= COST_ALERTS.monthly.critical) {
alerts.push({
level: 'critical',
message: `Monthly cost ${formatCost(monthlyTotal)} exceeds critical threshold ${formatCost(COST_ALERTS.monthly.critical)}`
});
} else if (monthlyTotal >= COST_ALERTS.monthly.warning) {
alerts.push({
level: 'warning',
message: `Monthly cost ${formatCost(monthlyTotal)} exceeds warning threshold ${formatCost(COST_ALERTS.monthly.warning)}`
});
}

return alerts;
}
