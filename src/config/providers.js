// src/config/providers.js
import { createOpenAI } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { createGoogleGenerativeAI } from '@ai-sdk/google';

// Enhanced provider configurations with fallback chains
export const providers = {
  // Primary OpenAI provider
  'gpt-4': {
    model: process.env.OPENAI_API_KEY ?
      createOpenAI({ apiKey: process.env.OPENAI_API_KEY })('gpt-4') : null,
    priority: 1,
    enabled: !!process.env.OPENAI_API_KEY,
    name: 'GPT-4',
    category: 'openai'
  },

  // OpenAI fallback: Perplexity
  'perplexity': {
    model: process.env.PERPLEXITY_API_KEY ?
      createOpenAI({
        baseURL: 'https://api.perplexity.ai/',
        apiKey: process.env.PERPLEXITY_API_KEY
      })('llama-3.1-sonar-small-128k-online') : null,
    priority: 2,
    enabled: !!process.env.PERPLEXITY_API_KEY,
    name: 'Perplexity Sonar',
    category: 'openai-fallback'
  },

  // Primary Anthropic provider
  'claude-sonnet': {
    model: process.env.ANTHROPIC_API_KEY ?
      anthropic('claude-3-5-sonnet-20241022') : null,
    priority: 3,
    enabled: !!process.env.ANTHROPIC_API_KEY,
    name: 'Claude Sonnet',
    category: 'anthropic'
  },

  // Anthropic fallback 1: Mistral (via OpenAI-compatible API)
  'hermes-2-pro-mistral': {
    model: process.env.MISTRAL_API_KEY ?
      createOpenAI({
        baseURL: 'process.env.MISTRAL_API_URL || "http://localhost:8080/v1"',
        apiKey: process.env.MISTRAL_API_KEY
      })('hermes-2-pro-hermes-2-pro-mistral') : null,
    priority: 3,
    enabled: !!(process.env.MISTRAL_API_URL && process.env.MISTRAL_API_KEY),
    name: 'Mistral (LocalAI)',
    category: 'anthropic-fallback'
  },

  // Anthropic fallback 2: Gemini
  'gemini-pro': {
    model: process.env.GOOGLE_GENERATIVE_AI_API_KEY ?
      createGoogleGenerativeAI({
        apiKey: process.env.GOOGLE_GENERATIVE_AI_API_KEY
      })('gemini-1.5-pro-latest') : null,
    priority: 5,
    enabled: !!process.env.GOOGLE_GENERATIVE_AI_API_KEY,
    name: 'Gemini Pro',
    category: 'anthropic-fallback'
  },

  // Anthropic fallback 3: Groq
  'groq-llama': {
    model: process.env.GROQ_API_KEY ?
      createOpenAI({
        baseURL: 'https://api.groq.com/openai/v1',
        apiKey: process.env.GROQ_API_KEY
      })('llama-3.1-70b-versatile') : null,
    priority: 6,
    enabled: !!process.env.GROQ_API_KEY,
    name: 'Groq Llama 3.1',
    category: 'anthropic-fallback'
  },

  // Local fallback (only enabled if explicitly configured)
  'hermes-2-pro-mistral-local': {
    model: (process.env.LOCALAI_HOST || process.env.LOCALAI_API_KEY) ?
      createOpenAI({
        baseURL: process.env.LOCALAI_HOST || 'http://localhost:8080/v1',
        apiKey: process.env.LOCALAI_API_KEY || 'localai'
      })('hermes-2-pro-mistral') : null,
    priority: 10,
    enabled: !!(process.env.LOCALAI_HOST || process.env.LOCALAI_API_KEY),
    name: 'Mistral Local',
    category: 'local'
  }
};

/**
 * Get provider with intelligent fallback based on original intent
 * @param {string} preferredCategory - 'openai', 'anthropic', or null for any
 * @returns {Object|null} The best available provider model
 */
export function getActiveProvider(preferredCategory = null) {
  const availableProviders = Object.entries(providers)
    .filter(([_, config]) => config.enabled && config.model)
    .sort(([_, a], [__, b]) => a.priority - b.priority);

  if (availableProviders.length === 0) {
    console.warn('❌ No AI providers are configured and available');
    return null;
  }

  // If preferred category specified, try category-specific fallback first
  if (preferredCategory) {
    // Try primary provider in category first
    const primaryProvider = availableProviders.find(
      ([_, config]) => config.category === preferredCategory
    );

    if (primaryProvider) {
      const [_name, config] = primaryProvider;
      console.log(`✅ Using preferred ${config.name} (${preferredCategory})`);
      return config.model;
    }

    // If primary not available, try fallbacks for that category
    const fallbackCategory = preferredCategory === 'openai' ? 'openai-fallback' : 'anthropic-fallback';
    const fallbackProvider = availableProviders.find(
      ([_, config]) => config.category === fallbackCategory
    );

    if (fallbackProvider) {
      const [_name, config] = fallbackProvider;
      console.log(`🔄 Falling back to ${config.name} (${config.category})`);
      return config.model;
    }
  }

  // Default: use highest priority available provider
  const [_name, config] = availableProviders[0];
  console.log(`🎯 Using best available provider: ${config.name} (priority: ${config.priority})`);
  return config.model;
}

/**
 * Get specific provider by name with fallback
 * @param {string} providerName - Name of the provider
 * @param {boolean} useFallback - Whether to use fallback if provider not available
 * @returns {Object|null} The provider model or fallback
 */
export function getProviderByName(providerName, useFallback = true) {
  const provider = providers[providerName];

  if (!provider) {
    console.warn(`❌ Provider ${providerName} not found`);
    return useFallback ? getActiveProvider() : null;
  }

  if (!provider.enabled || !provider.model) {
    console.warn(`❌ Provider ${providerName} (${provider.name}) is not available`);

    if (useFallback) {
      console.log(`🔄 Attempting fallback for ${providerName}...`);

      // OpenAI fallback chain: gpt-4 → perplexity → any available
      if (providerName === 'gpt-4') {
        return getActiveProvider('openai') || getActiveProvider();
      }

      // Anthropic fallback chain: claude → hermes-2-pro-mistral → gemini → groq → any available
      if (providerName === 'claude-sonnet') {
        return getActiveProvider('anthropic') || getActiveProvider();
      }

      // For other providers, use general fallback
      return getActiveProvider();
    }

    return null;
  }

  console.log(`✅ Using requested provider: ${provider.name}`);
  return provider.model;
}

/**
 * Get list of all available providers with status
 * @returns {Array} Array of available provider info
 */
export function getAvailableProviders() {
  return Object.entries(providers)
    .map(([key, config]) => ({
      key,
      name: config.name,
      category: config.category,
      priority: config.priority,
      enabled: config.enabled,
      available: config.enabled && !!config.model,
      status: config.enabled && config.model ? '✅ Available' :
        config.enabled ? '⚠️ Configured but not working' : '❌ Not configured'
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

/**
 * Get provider status summary for debugging
 * @returns {Object} Status summary
 */
export function getProviderStatus() {
  const available = getAvailableProviders();
  const total = available.length;
  const working = available.filter(p => p.available).length;
  const configured = available.filter(p => p.enabled).length;

  return {
    total,
    configured,
    working,
    hasAny: working > 0,
    providers: available,
    fallbackChains: {
      openai: ['gpt-4', 'perplexity'],
      anthropic: ['claude-sonnet', 'hermes-2-pro-mistral', 'gemini-pro', 'groq-llama'],
      local: ['hermes-2-pro-mistral-local']
    }
  };
}

const providersConfig = {
  providers,
  getActiveProvider,
    getProviderByName,
    getAvailableProviders,
    hasAvailableProvider,
    getProviderStatus
  };

export default providersConfig;
