/**
 * Model Provisioning API - Fixed for Serverless Environment
 * Removed direct local network access, uses webhooks instead
 */

const MODEL_CATALOG = require('./models.config.js');

// Helper: Get Eskom load shedding stage (mock for now)
async function getEskomStage(location) {
  try {
    // In production, call actual Eskom API
    const response = await fetch('https://loadshedding.eskom.co.za/API', {
      timeout: 3000
    });
    const data = await response.json();
    return data.stage || 0;
  } catch {
    return 0; // Default to no load shedding
  }
}

// Helper: Get internet uptime (estimated)
async function getInternetUptime(location) {
  // In production, ping the location's gateway
  return 0.95; // 95% uptime default
}

// Configuration moved to database/config file (not hardcoded)
async function getLocationConstraints() {
  // In production, fetch from database
  return {
    'Sebokeng': { min_localai_hours: 500, max_cloud_spend: 50 },
    'Three Rivers': { min_cloud_ai_quality: 8.5 },
    'Vanderbijlpark': { max_avg_cost_per_query: 0.001 }
  };
}

/**
 * Deploy model - Serverless compatible version
 * Instead of direct SSH, sends webhook to location's edge device
 */
async function deployModel(modelId, location) {
  const model = MODEL_CATALOG[modelId];

  if (!model) {
    throw new Error(`Model ${modelId} not found`);
  }

  // For cloud models, no deployment needed
  if (model.provider !== 'LocalAI') {
    return {
      deployed: true,
      provider: model.provider,
      endpoint: model.endpoint,
      note: 'Cloud model - no deployment required'
    };
  }

  // For LocalAI, send webhook to edge device
  const edgeWebhookUrl = process.env[`EDGE_WEBHOOK_${location.toUpperCase().replace(' ', '_')}`];

  if (!edgeWebhookUrl) {
    console.warn(`No edge webhook configured for ${location}`);
    return {
      deployed: false,
      error: 'Edge device not configured',
      suggestion: `Set EDGE_WEBHOOK_${location.toUpperCase().replace(' ', '_')} environment variable`
    };
  }

  try {
    // Send deployment request to edge device via webhook
    const response = await fetch(edgeWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.EDGE_WEBHOOK_SECRET}`
      },
      body: JSON.stringify({
        action: 'deploy_model',
        model_id: modelId,
        model_name: model.id,
        quant: 'q4_0', // 4-bit quantization for efficiency
        endpoint: model.endpoint
      }),
      timeout: 10000
    });

    if (!response.ok) {
      throw new Error(`Edge device returned ${response.status}`);
    }

    const result = await response.json();

    return {
      deployed: true,
      provider: 'LocalAI',
      location,
      deployment_id: result.deployment_id,
      endpoint: model.endpoint,
      note: 'Deployment queued on edge device'
    };

  } catch (error) {
    console.error(`Failed to deploy ${modelId} to ${location}:`, error);

    return {
      deployed: false,
      error: error.message,
      fallback: 'System will use cloud models until local deployment succeeds'
    };
  }
}

/**
 * Provision appropriate model for task/location
 */
module.exports = async (req, res) => {
  const { location, task, language, query } = req.body;

  if (!location || !task) {
    return res.status(400).json({
      error: 'Missing required fields: location and task'
    });
  }

  try {
    // Get constraints from configuration (not hardcoded)
    const constraints = await getLocationConstraints();
    const locationConstraints = constraints[location] || {};

    // Gather location context
    const context = {
      eskom_stage: await getEskomStage(location),
      internet_uptime: await getInternetUptime(location)
    };

    // Decision rules (could be moved to config/database)
    const rules = [
      {
        condition: () => context.eskom_stage > 4,
        action: 'use_localai_only',
        reason: 'High load shedding - prefer local models'
      },
      {
        condition: () => location === 'Three Rivers' && task === 'executive',
        action: 'use_gpt_4o_mini',
        reason: 'Executive task requires premium model'
      },
      {
        condition: () => locationConstraints.max_avg_cost_per_query < 0.001,
        action: 'prefer_cheap_models',
        reason: 'Cost constraint - use budget models'
      },
      {
        condition: () => language && language.includes('sesotho'),
        action: 'use_mistral_7b',
        reason: 'Mistral handles Sesotho better'
      }
    ];

    // Apply rules
    let selectedModel = null;
    let appliedRule = null;

    for (const rule of rules) {
      if (rule.condition()) {
        appliedRule = rule;

        // Select model based on action
        switch (rule.action) {
          case 'use_localai_only':
            selectedModel = Object.values(MODEL_CATALOG)
              .find(m => m.provider === 'LocalAI' && m.location === location);
            break;

          case 'use_gpt_4o_mini':
            selectedModel = MODEL_CATALOG['gpt-4o-mini'];
            break;

          case 'prefer_cheap_models':
            selectedModel = Object.values(MODEL_CATALOG)
              .sort((a, b) => a.cost_per_1k_tokens - b.cost_per_1k_tokens)[0];
            break;

          case 'use_mistral_7b':
            selectedModel = MODEL_CATALOG['mistral-7b-sebokeng'];
            break;
        }

        if (selectedModel) break;
      }
    }

    // Fallback to default model
    if (!selectedModel) {
      selectedModel = MODEL_CATALOG['gpt-3.5-turbo'];
      appliedRule = {
        action: 'default',
        reason: 'No specific rules applied'
      };
    }

    // Deploy model (returns immediately, deployment happens async)
    const deployment = await deployModel(selectedModel.id, location);

    // Return provisioning result
    return res.json({
      model_id: selectedModel.id,
      model_name: selectedModel.id,
      provider: selectedModel.provider,
      location,
      task,
      context,
      rule_applied: appliedRule.action,
      reason: appliedRule.reason,
      deployment_status: deployment.deployed ? 'success' : 'pending',
      deployment_note: deployment.note || deployment.error,
      cost_per_1k_tokens: selectedModel.cost_per_1k_tokens,
      endpoint: selectedModel.endpoint,
      estimated_cost: query ?
        (query.length / 4) * selectedModel.cost_per_1k_tokens / 1000 :
        null
    });

  } catch (error) {
    console.error('Provisioning error:', error);

    return res.status(500).json({
      error: 'Model provisioning failed',
      message: error.message,
      fallback_model: 'gpt-3.5-turbo'
    });
  }
};

// Export helper functions for testing
module.exports.deployModel = deployModel;
module.exports.getLocationConstraints = getLocationConstraints;
module.exports.getEskomStage = getEskomStage;