import { spawn } from 'child_process';
import { retryWithBackoff } from '../utils/retryWithBackoff.js';
import { MODEL_CATALOG } from '../models.config.js';
import { sql } from '@vercel/postgres';
import { Counter } from 'prom-client';
import logger from '../utils/logger.js';

const modelRequestCounter = new Counter({
  name: 'model_requests_total',
  help: 'Total number of requests for a specific model',
  labelNames: ['model'],
});

// ✅ Input validation schema
function validateUsageData(result, model) {
  if (!result || typeof result !== 'object') {
    throw new Error('Invalid result object');
  }

  if (!result.usage || typeof result.usage.total_tokens !== 'number') {
    throw new Error('Invalid usage data: total_tokens missing or invalid');
  }

  if (typeof model.cost_per_1k_tokens !== 'number') {
    throw new Error('Invalid model configuration: cost_per_1k_tokens missing');
  }

  return {
    totalTokens: Math.max(0, Math.floor(result.usage.total_tokens)),
    costUsd: (result.usage.total_tokens * model.cost_per_1k_tokens) / 1000
  };
}


// ✅ FIX: Shell injection prevention for CrewAI
async function executeCrewAIScript(model, query) {
  const { spawn } = await import('child_process');

  // ✅ Input sanitization - whitelist allowed characters
  const sanitizedQuery = query.replace(/[^a-zA-Z0-9\s.,?!-]/g, '');

  if (sanitizedQuery !== query) {
    logger.warn('Query contained potentially dangerous characters - sanitized');
  }

  // ✅ Validate script path
  const allowedScripts = [
    '/app/scripts/crewai_task.py',
    '/app/scripts/crewai_agent.py',
    'crewai/main.py'
  ];

  if (!allowedScripts.includes(model.script)) {
    throw new Error(`Invalid script path: ${model.script}`);
  }

  return new Promise((resolve, reject) => {
    // ✅ Use array of arguments - prevents shell injection
    const pythonProcess = spawn('python3', [model.script], {
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 30000
    });

    // Send query via stdin instead of command line
    pythonProcess.stdin.write(JSON.stringify({ query: sanitizedQuery }));
    pythonProcess.stdin.end();

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const parsedOutput = JSON.parse(output);
           if (parsedOutput.error) {
                return reject(new Error(`CrewAI script error: ${parsedOutput.error}`));
            }
            resolve({
                response: parsedOutput.result,
                usage: {
                    total_tokens: parsedOutput.token_usage?.total_tokens || 0
                }
            });
        } catch (e) {
          reject(new Error(`Invalid JSON output: ${output}`));
        }
      } else {
        reject(new Error(`Script failed with code ${code}: ${errorOutput}`));
      }
    });

    pythonProcess.on('error', reject);
  });
}

async function makeModelRequest(model, payload) {
    const modelId = Object.keys(MODEL_CATALOG).find(key => MODEL_CATALOG[key] === model);

    if (model.provider === 'LocalAI') {
        const response = await retryWithBackoff(async () => {
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
            return res.json();
        });
        return {
            response: response?.choices?.[0]?.text,
            usage: {
                total_tokens: response?.usage?.total_tokens || 0
            }
        };
    }

    if (model.provider === 'OpenAI' || model.provider === 'Groq') {
        const response = await retryWithBackoff(async () => {
            const res = await fetch(model.endpoint, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${process.env[model.api_key_env]}`
                },
                body: JSON.stringify({
                    model: modelId,
                    messages: [{
                        role: 'user',
                        content: payload.query
                    }],
                    max_tokens: 500
                })
            });
            if (!res.ok) {
                const errorBody = await res.text();
                throw new Error(`${model.provider} API error (${res.status}): ${errorBody}`);
            }
            return res.json();
        });
        return {
            response: response?.choices?.[0]?.message?.content,
            usage: {
                total_tokens: response?.usage?.total_tokens || 0
            }
        };
    }

    if (model.provider === 'Anthropic') {
        const response = await retryWithBackoff(async () => {
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
                    messages: [{
                        role: 'user',
                        content: payload.query
                    }]
                })
            });
            if (!res.ok) {
                const errorBody = await res.text();
                throw new Error(`Anthropic API error (${res.status}): ${errorBody}`);
            }
            return res.json();
        });
        return {
            response: response?.content?.[0]?.text,
            usage: {
                total_tokens: (response?.usage?.input_tokens || 0) + (response?.usage?.output_tokens || 0)
            }
        };
    }

    if (model.provider === 'Cohere') {
        const response = await retryWithBackoff(async () => {
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
            return res.json();
        });
        return {
            response: response.embeddings,
            usage: {
                total_tokens: (response?.meta?.billed_units?.input_tokens || 0) + (response?.meta?.billed_units?.output_tokens || 0)
            }
        };
    }

    if (model.provider === 'CrewAI') {
        return executeCrewAIScript(model, payload.query);
    }
}


export default async function handler(req, res) {
  try {
    const { model_id, location, task, client_id } = req.body;

    // ✅ Input validation
    if (!model_id || !location || !task) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Get model configuration
    const model = MODEL_CATALOG[model_id];
    if (!model) {
      return res.status(404).json({ error: 'Model not found' });
    }

    // Make model request
    const result = await makeModelRequest(model, req.body);

    // ✅ Validate and sanitize data before SQL insert
    const { totalTokens, costUsd } = validateUsageData(result, model);

    // Increment Prometheus counter
    modelRequestCounter.inc({ model: model_id });

    // ✅ Parameterized query with validated inputs
    await sql`
      INSERT INTO model_usage_logs
      (model_id, location, task, tokens_used, cost_usd, client_id, created_at)
      VALUES
      (${model_id}, ${location}, ${task}, ${totalTokens}, ${costUsd}, ${client_id || 'anonymous'}, NOW())
    `;

    res.json({
      model_used: model_id,
      tokens_used: totalTokens,
      cost_usd: costUsd,
      response: result.response
    });

  } catch (error) {
    logger.error('Orchestrator error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}
