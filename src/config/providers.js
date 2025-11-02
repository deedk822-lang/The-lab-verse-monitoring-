// src/config/providers.js
import { createOpenAI } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';

// LocalAI (Mistral-7B) - OpenAI-compatible
export const mistralLocal = createOpenAI({
  baseURL: process.env.LOCALAI_HOST || 'http://localhost:8080/v1',
  apiKey: process.env.LOCALAI_API_KEY || 'localai',
});

// Provider configurations with priority
export const providers = {
  'mistral-local': {
    model: mistralLocal('mistral'),
    priority: 1,
    enabled: true,
    name: 'Mistral Local'
  },
  'gpt-4': {
    model: process.env.OPENAI_API_KEY ?
      createOpenAI({ apiKey: process.env.OPENAI_API_KEY })('gpt-4') : null,
    priority: 2,
    enabled: !!process.env.OPENAI_API_KEY,
    name: 'GPT-4'
  },
  'claude-sonnet': {
    model: process.env.ANTHROPIC_API_KEY ?
      anthropic('claude-3-5-sonnet-20241022') : null,
    priority: 3,
    enabled: !!process.env.ANTHROPIC_API_KEY,
    name: 'Claude Sonnet'
  }
};

/**
 * Get the first available provider based on priority
 * @returns {Object|null} The active provider model or null
 */
export function getActiveProvider() {
  const sortedProviders = Object.entries(providers)
    .filter(([_, config]) => config.enabled && config.model)
    .sort(([_, a], [__, b]) => a.priority - b.priority);

  if (sortedProviders.length === 0) {
    console.warn('No AI providers are configured and enabled');
    return null;
  }

  const [name, config] = sortedProviders[0];
  console.log(`Using AI provider: ${config.name} (priority: ${config.priority})`);

  return config.model;
}

/**
 * Get provider by name
 * @param {string} providerName - Name of the provider
 * @returns {Object|null} The provider model or null
 */
export function getProviderByName(providerName) {
  const provider = providers[providerName];

  if (!provider) {
    console.warn(`Provider ${providerName} not found`);
    return null;
  }

  if (!provider.enabled) {
    console.warn(`Provider ${providerName} is not enabled`);
    return null;
  }

  return provider.model;
}

/**
 * Get list of all available providers
 * @returns {Array} Array of available provider names
 */
export function getAvailableProviders() {
  return Object.entries(providers)
    .filter(([_, config]) => config.enabled && config.model)
    .map(([name, config]) => ({
      name,
      displayName: config.name,
      priority: config.priority
    }))
    .sort((a, b) => a.priority - b.priority);
}

/**
 * Check if any provider is available
 * @returns {boolean} True if at least one provider is available
 */
export function hasAvailableProvider() {
  return Object.values(providers).some(config => config.enabled && config.model);
}

export default {
  mistralLocal,
  providers,
  getActiveProvider,
  getProviderByName,
  getAvailableProviders,
  hasAvailableProvider
};