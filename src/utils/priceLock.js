// src/utils/priceLock.js
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const baseline = require('../../config/price-baseline.json');

export function maxCostPer1M(provider) {
  return baseline.baseline.providers[provider]?.costPer1M ?? Infinity;
}

export function monthlyBudget() {
  return baseline.baseline.softLimits.monthlyTotal;
}
