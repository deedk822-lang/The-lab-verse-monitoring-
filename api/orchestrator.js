/**
 * AI Model Orchestrator - Fixed Version
 * Refactored with Strategy Pattern and removed code duplication
 */

const MODEL_CATALOG = require('./models/models.config.js');

// Helper function to calculate cost (eliminates duplication)
function calculateCost(totalTokens, costPer1kTokens) {
  return (totalTokens * costPer1kTokens) / 1000;
}

// Provider Strategy Pattern
class ProviderStrategy {
  constructor(model) {
    this.model = model;
  }

  async execute(modelId, payload) {
    throw new Error('Execute method must be implemented');
  }

  async checkHealth(modelId) {
    throw new Error('CheckHealth method must be implemented');
  }
}

class LocalAIProvider extends ProviderStrategy {
  async execute(modelId, payload) {
    const res = await fetch(this.model.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelId,
        prompt: payload.query,
        temperature: 0.7
      }),
      timeout: 30000
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`LocalAI error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response?.choices?.[0]?.text || response?.text,
      usage: {
        total_tokens: response?.usage?.total_tokens || 0
      }
    };
  }

  async checkHealth(modelId) {
    const baseUrl = this.model.endpoint.replace(/\/v1\/.*$/, '');
    try {
      const r = await fetch(`${baseUrl}/health`, { timeout: 2000 });
      return r.ok;
    } catch {
      return false;
    }
  }
}

class OpenAIProvider extends ProviderStrategy {
  async execute(modelId, payload) {
    const res = await fetch(this.model.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env[this.model.api_key_env]}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: modelId,
        messages: [{ role: 'user', content: payload.query }],
        max_tokens: 500
      }),
      timeout: 30000
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`OpenAI/Groq error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response?.choices?.[0]?.message?.content,
      usage: {
        total_tokens: response?.usage?.total_tokens || 0
      }
    };
  }

  async checkHealth(modelId) {
    try {
      const response = await fetch(this.model.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env[this.model.api_key_env]}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: modelId,
          messages: [{ role: 'user', content: 'test' }],
          max_tokens: 1
        }),
        timeout: 5000
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

class AnthropicProvider extends ProviderStrategy {
  async execute(modelId, payload) {
    const res = await fetch(this.model.endpoint, {
      method: 'POST',
      headers: {
        'x-api-key': process.env[this.model.api_key_env],
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: modelId,
        max_tokens: 500,
        messages: [{ role: 'user', content: payload.query }]
      }),
      timeout: 30000
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`Anthropic API error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response?.content?.[0]?.text,
      usage: {
        total_tokens: (response?.usage?.input_tokens || 0) + (response?.usage?.output_tokens || 0)
      }
    };
  }

  async checkHealth(modelId) {
    try {
      const response = await fetch(this.model.endpoint, {
        method: 'POST',
        headers: {
          'x-api-key': process.env[this.model.api_key_env],
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          model: modelId,
          max_tokens: 1,
          messages: [{ role: 'user', content: 'test' }]
        }),
        timeout: 5000
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

class CohereProvider extends ProviderStrategy {
  async execute(modelId, payload) {
    const res = await fetch(this.model.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env[this.model.api_key_env]}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        texts: [payload.query],
        model: modelId,
        input_type: 'search_document'
      }),
      timeout: 30000
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`Cohere API error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response?.embeddings || [],
      usage: {
        total_tokens: (response?.meta?.billed_units?.input_tokens || 0) +
                     (response?.meta?.billed_units?.output_tokens || 0)
      }
    };
  }

  async checkHealth(modelId) {
    try {
      const response = await fetch(this.model.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env[this.model.api_key_env]}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          texts: ['test'],
          model: modelId,
          input_type: 'search_document'
        }),
        timeout: 5000
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Provider Factory
class ProviderFactory {
  static create(model) {
    const providerMap = {
      'LocalAI': LocalAIProvider,
      'OpenAI': OpenAIProvider,
      'Groq': OpenAIProvider, // Groq uses OpenAI-compatible API
      'Anthropic': AnthropicProvider,
      'Cohere': CohereProvider
    };

    const ProviderClass = providerMap[model.provider];
    if (!ProviderClass) {
      throw new Error(`Unknown provider: ${model.provider}`);
    }

    return new ProviderClass(model);
  }
}

// Main orchestration functions
async function executeOnModel(modelId, payload, client_id = null) {
  const model = MODEL_CATALOG[modelId];
  if (!model) {
    throw new Error(`Model ${modelId} not found in catalog`);
  }

  const provider = ProviderFactory.create(model);
  const result = await provider.execute(modelId, payload);

  // Calculate cost once using helper function
  const cost = calculateCost(result.usage.total_tokens, model.cost_per_1k_tokens);

  // Log usage (if database available)
  if (client_id && global.db) {
    await global.db.query(`
      INSERT INTO model_usage_logs (model_id, location, task, tokens_used, cost_usd, client_id, timestamp)
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
    `, [modelId, payload.location, payload.task, result.usage.total_tokens, cost, client_id]);
  }

  return {
    model_used: modelId,
    result: result.output,
    cost_usd: cost,
    usage: result.usage,
    timestamp: new Date().toISOString()
  };
}

async function checkModelHealth(modelId) {
  const model = MODEL_CATALOG[modelId];
  if (!model) {
    return false;
  }

  try {
    const provider = ProviderFactory.create(model);
    return await provider.checkHealth(modelId);
  } catch (error) {
    console.error(`Health check failed for ${modelId}:`, error);
    return false;
  }
}

// API Handler
module.exports = async (req, res) => {
  const { model_id, task, location, query, client_id } = req.body;

  if (!model_id || !query) {
    return res.status(400).json({
      error: 'Missing required fields: model_id and query'
    });
  }

  try {
    // Check model health first
    const isHealthy = await checkModelHealth(model_id);

    if (!isHealthy) {
      return res.status(503).json({
        error: `Model ${model_id} is currently unavailable`,
        suggestion: 'Try a different model or retry later'
      });
    }

    // Execute on model
    const result = await executeOnModel(
      model_id,
      { task, location, query },
      client_id
    );

    return res.json(result);

  } catch (error) {
    console.error('Orchestration error:', error);

    return res.status(500).json({
      error: 'Model execution failed',
      message: error.message,
      model_id
    });
  }
};

// Export functions for testing
module.exports.executeOnModel = executeOnModel;
module.exports.checkModelHealth = checkModelHealth;
module.exports.calculateCost = calculateCost;
module.exports.ProviderFactory = ProviderFactory;