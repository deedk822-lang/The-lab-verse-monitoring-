// src/providers/multiProviderFallback.js
// Multi-provider fallback chain with native SDK support

import { generateGroq, promptToMessages } from './groqProvider.js';
import { generateContent } from '../services/contentGenerator.js';

/**
 * Provider configurations for fallback chain
 */
const providers = [
  { 
    name: 'OpenAI', 
    fn: async ({ messages, temperature, max_tokens }) => {
      // Convert messages to simple prompt for existing contentGenerator
      const prompt = messages[messages.length - 1]?.content || '';
      return await generateContent(prompt, {
        provider: 'gpt-4',
        temperature,
        maxTokens: max_tokens
      });
    },
    env: 'OPENAI_API_KEY' 
  },
  { 
    name: 'Groq',
    fn: generateGroq,
    env: 'GROQ_API_KEY'
  },
  { 
    name: 'Perplexity',
    fn: async ({ messages, temperature, max_tokens }) => {
      const prompt = messages[messages.length - 1]?.content || '';
      return await generateContent(prompt, {
        provider: 'perplexity',
        temperature,
        maxTokens: max_tokens
      });
    },
    env: 'PERPLEXITY_API_KEY' 
  },
  { 
    name: 'Gemini',
    fn: async ({ messages, temperature, max_tokens }) => {
      const prompt = messages[messages.length - 1]?.content || '';
      return await generateContent(prompt, {
        provider: 'gemini-pro',
        temperature,
        maxTokens: max_tokens
      });
    },
    env: 'GOOGLE_GENERATIVE_AI_API_KEY' 
  }
];

/**
 * Multi-provider generate with automatic fallback
 * @param {string|Array} input - Either a simple prompt string or messages array
 * @param {Object} options - Generation options
 * @param {number} options.temperature - Temperature for generation (default: 0.7)
 * @param {number} options.max_tokens - Maximum tokens (default: 1024)
 * @param {boolean} options.stopOnFirst - Stop on first success (default: true)
 * @returns {Promise<Object>} Result with provider name and generated text
 */
export async function multiProviderGenerate(input, options = {}) {
  // Convert input to messages format if needed
  const messages = Array.isArray(input) ? input : promptToMessages(input);
  
  const temperature = options.temperature || 0.7;
  const max_tokens = options.max_tokens || 1024;
  const stopOnFirst = options.stopOnFirst !== false;

  const errors = [];
  
  for (const p of providers) {
    // Skip if API key not configured
    if (!process.env[p.env]) {
      console.log(`⚠️  ${p.name} skipped: ${p.env} not configured`);
      continue;
    }
    
    try {
      console.log(`🔄 Trying ${p.name}...`);
      
      const text = await p.fn({ messages, temperature, max_tokens });
      
      if (text) {
        console.log(`✅ ${p.name} succeeded`);
        return { 
          provider: p.name, 
          text,
          success: true,
          errors: errors.length > 0 ? errors : undefined
        };
      }
    } catch (e) {
      const errorMsg = `${p.name} failed: ${e.message}`;
      console.warn(`⚠️  ${errorMsg}`);
      errors.push({ provider: p.name, error: e.message });
      
      if (!stopOnFirst) {
        continue;
      }
    }
  }
  
  throw new Error(`All providers exhausted. Errors: ${JSON.stringify(errors)}`);
}

/**
 * Test all configured providers
 * @returns {Promise<Object>} Test results for each provider
 */
export async function testAllProviders() {
  const testPrompt = 'Say "Hello from" followed by your model name in 5 words or less.';
  const results = {};
  
  console.log('\n🧪 Testing all configured providers...\n');
  
  for (const p of providers) {
    if (!process.env[p.env]) {
      results[p.name] = { 
        status: '⚠️ Not Configured', 
        env: p.env,
        configured: false 
      };
      continue;
    }
    
    try {
      const messages = promptToMessages(testPrompt);
      const startTime = Date.now();
      
      const text = await p.fn({ 
        messages, 
        temperature: 0.7, 
        max_tokens: 50 
      });
      
      const duration = Date.now() - startTime;
      
      results[p.name] = { 
        status: '✅ Success',
        response: text.substring(0, 100),
        duration: `${duration}ms`,
        configured: true,
        working: true
      };
    } catch (error) {
      results[p.name] = { 
        status: '❌ Failed',
        error: error.message,
        configured: true,
        working: false
      };
    }
  }
  
  return results;
}

/**
 * Get list of available providers
 * @returns {Array<Object>} List of provider info
 */
export function getAvailableProviders() {
  return providers.map(p => ({
    name: p.name,
    envVar: p.env,
    configured: !!process.env[p.env],
    available: !!process.env[p.env]
  }));
}

export default {
  multiProviderGenerate,
  testAllProviders,
  getAvailableProviders
};
