/**
 * Budget Allocation API - Fixed Version
 * Constraints moved to configuration, not hardcoded
 */

const MODEL_CATALOG = require('../models/models.config.js');

// Load constraints from environment/config (not hardcoded)
function loadBudgetConstraints() {
  // Try to load from environment first
  const constraintsEnv = process.env.BUDGET_CONSTRAINTS;

  if (constraintsEnv) {
    try {
      return JSON.parse(constraintsEnv);
    } catch (error) {
      console.error('Failed to parse BUDGET_CONSTRAINTS env var:', error);
    }
  }

  // Fallback to default configuration
  // In production, load from database or config service
  return {
    'Sebokeng': {
      min_localai_hours: 500,
      max_cloud_spend: 50, // R50/month cloud
      currency: 'ZAR'
    },
    'Three Rivers': {
      min_cloud_ai_quality: 8.5, // Only premium models
      min_uptime: 0.99
    },
    'Vanderbijlpark': {
      max_avg_cost_per_query: 0.001, // Ultra-cheap
      prefer_local: true
    }
  };
}

// Calculate optimal budget allocation
function calculateOptimalAllocation(budget, constraints, historicalUsage) {
  const allocation = {
    local_ai: 0,
    cloud_ai: 0,
    storage: 0,
    bandwidth: 0,
    contingency: 0
  };

  // Apply constraints
  if (constraints.min_localai_hours) {
    // Estimate local AI infrastructure cost
    const localCostPerHour = 0.10; // R0.10 per hour (electricity + Pi cost amortized)
    allocation.local_ai = constraints.min_localai_hours * localCostPerHour;
  }

  if (constraints.max_cloud_spend) {
    allocation.cloud_ai = Math.min(
      budget * 0.5, // Max 50% on cloud
      constraints.max_cloud_spend
    );
  } else {
    allocation.cloud_ai = budget * 0.4; // Default 40% on cloud
  }

  // Allocate remaining budget
  const allocated = allocation.local_ai + allocation.cloud_ai;
  const remaining = budget - allocated;

  allocation.storage = remaining * 0.2; // 20% for storage
  allocation.bandwidth = remaining * 0.3; // 30% for bandwidth
  allocation.contingency = remaining * 0.5; // 50% contingency

  return allocation;
}

// Optimize model selection based on budget
function optimizeModelSelection(budget, constraints, usage_pattern) {
  const models = Object.values(MODEL_CATALOG);

  // Filter models based on constraints
  let eligibleModels = models;

  if (constraints.min_cloud_ai_quality) {
    eligibleModels = eligibleModels.filter(m =>
      !m.quality_score || m.quality_score >= constraints.min_cloud_ai_quality
    );
  }

  if (constraints.max_avg_cost_per_query) {
    eligibleModels = eligibleModels.filter(m =>
      m.cost_per_1k_tokens / 1000 <= constraints.max_avg_cost_per_query
    );
  }

  if (constraints.prefer_local) {
    // Prioritize LocalAI models
    eligibleModels.sort((a, b) => {
      if (a.provider === 'LocalAI' && b.provider !== 'LocalAI') return -1;
      if (a.provider !== 'LocalAI' && b.provider === 'LocalAI') return 1;
      return a.cost_per_1k_tokens - b.cost_per_1k_tokens;
    });
  } else {
    // Sort by cost-effectiveness
    eligibleModels.sort((a, b) => {
      const scoreA = (a.quality_score || 5) / a.cost_per_1k_tokens;
      const scoreB = (b.quality_score || 5) / b.cost_per_1k_tokens;
      return scoreB - scoreA; // Higher score first
    });
  }

  return eligibleModels.slice(0, 5); // Top 5 models
}

// Main API handler
module.exports = async (req, res) => {
  const {
    budget,
    location,
    time_period = 'monthly',
    historical_usage = {}
  } = req.body;

  if (!budget || !location) {
    return res.status(400).json({
      error: 'Missing required fields: budget and location'
    });
  }

  try {
    // Load constraints (from config, not hardcoded)
    const allConstraints = loadBudgetConstraints();
    const constraints = allConstraints[location] || {};

    // Calculate optimal allocation
    const allocation = calculateOptimalAllocation(
      budget,
      constraints,
      historical_usage
    );

    // Get recommended models
    const recommendedModels = optimizeModelSelection(
      budget,
      constraints,
      historical_usage.pattern || 'balanced'
    );

    // Calculate projected usage
    const projectedQueries = historical_usage.queries_per_month || 10000;
    const avgQueryTokens = historical_usage.avg_tokens_per_query || 500;

    const projectedCost = {
      optimistic: 0,
      realistic: 0,
      pessimistic: 0
    };

    // Use cheapest model for optimistic
    if (recommendedModels.length > 0) {
      const cheapest = recommendedModels[recommendedModels.length - 1];
      projectedCost.optimistic = (projectedQueries * avgQueryTokens * cheapest.cost_per_1k_tokens) / 1000;

      // Use mid-tier model for realistic
      const midTier = recommendedModels[Math.floor(recommendedModels.length / 2)];
      projectedCost.realistic = (projectedQueries * avgQueryTokens * midTier.cost_per_1k_tokens) / 1000;

      // Use premium model for pessimistic
      const premium = recommendedModels[0];
      projectedCost.pessimistic = (projectedQueries * avgQueryTokens * premium.cost_per_1k_tokens) / 1000;
    }

    // Budget health assessment
    const health = {
      status: 'healthy',
      warnings: [],
      recommendations: []
    };

    if (projectedCost.realistic > budget) {
      health.status = 'at_risk';
      health.warnings.push(`Projected realistic cost (${projectedCost.realistic.toFixed(2)}) exceeds budget (${budget})`);
      health.recommendations.push('Consider increasing budget or reducing query volume');
    }

    if (allocation.contingency < budget * 0.1) {
      health.warnings.push('Low contingency buffer');
      health.recommendations.push('Increase budget or reduce fixed costs');
    }

    // Return optimization result
    return res.json({
      budget,
      location,
      time_period,
      allocation,
      constraints_applied: constraints,
      recommended_models: recommendedModels.map(m => ({
        id: m.id,
        provider: m.provider,
        cost_per_1k_tokens: m.cost_per_1k_tokens,
        quality_score: m.quality_score,
        reason: m.provider === 'LocalAI' ? 'Low cost, local processing' : 'Best cost-performance ratio'
      })),
      projected_cost: projectedCost,
      budget_health: health,
      optimization_tips: [
        constraints.prefer_local ? 'Using local models where possible to reduce costs' : null,
        projectedCost.realistic < budget * 0.8 ? 'Budget has headroom for higher quality models' : null,
        'Monitor actual usage and adjust allocation monthly'
      ].filter(Boolean),
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Budget allocation error:', error);

    return res.status(500).json({
      error: 'Budget optimization failed',
      message: error.message
    });
  }
};

// Export helper functions for testing
module.exports.loadBudgetConstraints = loadBudgetConstraints;
module.exports.calculateOptimalAllocation = calculateOptimalAllocation;
module.exports.optimizeModelSelection = optimizeModelSelection;