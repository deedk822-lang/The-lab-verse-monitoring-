// src/config/providers.js
import { createOpenAI } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';

// LocalAI (Mistral-7B) - OpenAI-compatible
export const mistralLocal = createOpenAI({
  baseURL: process.env.LOCALAI_HOST || 'http://localhost:8080/v1',
  apiKey: process.env.LOCALAI_API_KEY || 'localai',
});

// Cloud providers (optional fallbacks)
export const providers = {
  'mistral-local': {
    model: mistralLocal('mistral'),
    priority: 1,
    enabled: true
  },
  'gpt-4': {
    model: createOpenAI({ apiKey: process.env.OPENAI_API_KEY })('gpt-4'),
    priority: 2,
    enabled: !!process.env.OPENAI_API_KEY
  },
  'claude-sonnet': {
    model: anthropic('claude-3-5-sonnet-20241022'),
    priority: 3,
    enabled: !!process.env.ANTHROPIC_API_KEY
  }
};

// Get first available provider
export function getActiveProvider() {
  return Object.entries(providers)
    .sort(([, a], [, b]) => a.priority - b.priority)
    .find(([, config]) => config.enabled)?.[1]?.model;
}
