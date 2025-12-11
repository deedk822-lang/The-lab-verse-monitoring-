import { MODEL_CATALOG } from '../models.config.js';
import { sql } from '@vercel/postgres';

export default async function handler(req, res) {
  const { task, location, language, student_id: client_id } = req.body;

  // 1. Determine which model to use
  let model_id;
  switch (task) {
    case 'content_generation':
      model_id = location === 'Sebokeng' ? 'mistral-7b-instruct-v0.2-q4' : 'mixtral-8x7b-together';
      break;
    case 'job_matching':
      model_id = 'llama-3.1-8b-groq'; // Fast & cheap
      break;
    case 'compliance_analysis':
      model_id = 'claude-3.5-sonnet'; // Best for legal docs
      break;
    case 'executive_coaching':
      model_id = 'gpt-4o-mini'; // Premium
      break;
    case 'code_assistance':
      model_id = location === 'Vanderbijlpark' ? 'qwen2.5-coder-1.5b-q4' : 'gpt-4o-mini';
      break;
    case 'rag_embeddings':
      model_id = 'cohere-embed-multilingual';
      break;
    default:
      model_id = 'mistral-7b-instruct-v0.2-q4'; // Default safe choice
  }

  let model = MODEL_CATALOG[model_id];

  // 2. Check if model is healthy
  const is_healthy = await checkModelHealth(model_id);

  if (!is_healthy) {
    // Fallback to LocalAI mistral if cloud fails
    model_id = 'mistral-7b-instruct-v0.2-q4';
    model = MODEL_CATALOG[model_id];
  }

  // 3. Execute on the specific model
  const result = await executeOnModel(model_id, req.body);

  // 4. Log cost for this query
  await sql`
    INSERT INTO model_usage_logs
    (model_id, location, task, tokens_used, cost_usd, client_id)
    VALUES
    (${model_id}, ${location}, ${task}, ${result.usage.total_tokens},
     ${result.usage.total_tokens * model.cost_per_1k_tokens / 1000}, ${client_id})
  `;

  res.json({
    model_used: model_id,
    result: result.output,
    cost_usd: result.usage.total_tokens * model.cost_per_1k_tokens / 1000,
    human_review_needed: model.capability < 7.0 // Flag if low-confidence
  });
}

async function executeOnModel(modelId, payload) {
  const model = MODEL_CATALOG[modelId];

  // Route to correct provider
  if (model.provider === 'LocalAI') {
    const res = await fetch(model.endpoint, {
      method: 'POST',
      body: JSON.stringify({
        model: modelId,
        prompt: payload.query,
        max_tokens: 500,
        temperature: 0.3
      })
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`LocalAI API error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response?.choices?.[0]?.text,
      usage: {
        total_tokens: response?.usage?.total_tokens || 0
      }
    };
  }

  if (model.provider === 'OpenAI' || model.provider === 'Groq') {
    const res = await fetch(model.endpoint, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${process.env[model.api_key_env]}` },
      body: JSON.stringify({
        model: modelId,
        messages: [{ role: 'user', content: payload.query }],
        max_tokens: 500
      })
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`${model.provider} API error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response?.choices?.[0]?.message?.content,
      usage: {
        total_tokens: response?.usage?.total_tokens || 0
      }
    };
  }

  if (model.provider === 'Anthropic') {
    const res = await fetch(model.endpoint, {
      method: 'POST',
      headers: {
        'x-api-key': process.env[model.api_key_env],
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: modelId,
        max_tokens: 500,
        messages: [{ role: 'user', content: payload.query }]
      })
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

  if (model.provider === 'Cohere') {
    const res = await fetch(model.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env[model.api_key_env]}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        texts: [payload.query],
        model: modelId,
        input_type: 'search_document'
      })
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`Cohere API error (${res.status}): ${errorBody}`);
    }

    const response = await res.json();
    return {
      output: response.embeddings,
      usage: {
        total_tokens: (response?.meta?.billed_units?.input_tokens || 0) + (response?.meta?.billed_units?.output_tokens || 0)
      }
    };
  }
}

async function checkModelHealth(modelId) {
    const model = MODEL_CATALOG[modelId];

    if (model.provider === 'LocalAI') {
        const baseUrl = model.endpoint.replace(/\/v1\/.*$/, '');
        try {
            const r = await fetch(`${baseUrl}/health`, { timeout: 2000 });
            return r.ok;
        } catch {
            return false;
        }
    } else {
        try {
            const response = await fetch(model.endpoint, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${process.env[model.api_key_env]}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: modelId,
                    messages: [{ role: 'user', content: 'test' }],
                    max_tokens: 1
                })
            });
            return response.ok;
        } catch {
            return false;
        }
    }
}
