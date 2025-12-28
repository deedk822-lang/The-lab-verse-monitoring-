// models.config.js - FIXED
import logger from './utils/logger.js';

// ✅ Validate required environment variables at startup
const REQUIRED_ENV_VARS = ['LOCALAI_ENDPOINT'];

function validateEnvironment() {
  const missing = REQUIRED_ENV_VARS.filter(varName => !process.env[varName]);

  if (missing.length > 0) {
    logger.error(`❌ Missing required environment variables: ${missing.join(', ')}`);
    throw new Error(`Configuration error: Missing ${missing.join(', ')}`);
  }
}

// Validate on module load
validateEnvironment();

export const MODEL_CATALOG = {
  // ** TIER 1: LocalAI-Compatible (Loadshedding-Proof) **
  'mistral-7b-instruct-v0.2-q4': {
    provider: 'LocalAI',
    endpoint: `${process.env.LOCALAI_ENDPOINT}/v1/chat/completions`, // ✅ No fallback
    cost_per_1k_tokens: 0.0000,
    capability: 6.5,
    specialization: 'content_generation',
    languages: ['en', 'af', 'nso', 'st'],
    timeout: 30000, // 30 seconds
  },
  // Add more models...
};

// ✅ Connection validation function
export async function validateModelConnections() {
  const results = [];

  for (const [modelId, config] of Object.entries(MODEL_CATALOG)) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(config.endpoint.replace('/chat/completions', '/models'), {
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        results.push({ modelId, status: 'healthy' });
        logger.info(`✅ Model ${modelId} endpoint validated`);
      } else {
        results.push({ modelId, status: 'unhealthy', error: response.statusText });
        logger.error(`❌ Model ${modelId} endpoint returned ${response.status}`);
      }
    } catch (error) {
      results.push({ modelId, status: 'unreachable', error: error.message });
      logger.error(`❌ Model ${modelId} endpoint unreachable: ${error.message}`);
    }
  }

  return results;
}
