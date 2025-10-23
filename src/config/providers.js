import dotenv from 'dotenv';

dotenv.config();

export const PROVIDERS = {
  OPENAI: 'openai',
  GOOGLE: 'google',
  LOCALAI: 'localai',
  ZAI: 'zai'
};

export const PROVIDER_CONFIGS = {
  [PROVIDERS.OPENAI]: {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    apiKey: process.env.OPENAI_API_KEY,
    models: {
      text: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
      image: ['dall-e-3', 'dall-e-2'],
      audio: ['tts-1', 'tts-1-hd', 'whisper-1']
    },
    capabilities: ['text', 'image', 'audio', 'vision'],
    maxTokens: 128000,
    costPerToken: 0.00003
  },
  
  [PROVIDERS.GOOGLE]: {
    name: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    apiKey: process.env.GOOGLE_API_KEY,
    models: {
      text: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro'],
      image: ['imagen-3.0-generate-001', 'imagen-3.0-generate-002'],
      video: ['veo-3.1-generate-001'],
      audio: ['texttospeech', 'speech-to-text']
    },
    capabilities: ['text', 'image', 'video', 'audio', 'vision', 'search', 'maps'],
    maxTokens: 2000000,
    costPerToken: 0.00001,
    projectId: process.env.GOOGLE_PROJECT_ID,
    location: process.env.GOOGLE_LOCATION || 'us-central1'
  },
  
  [PROVIDERS.LOCALAI]: {
    name: 'LocalAI',
    baseUrl: process.env.LOCALAI_URL || 'http://localhost:8080',
    apiKey: process.env.LOCALAI_API_KEY,
    models: {
      text: [process.env.LOCALAI_MODEL || 'llama-3.2-1b-instruct'],
      image: [process.env.LOCALAI_IMAGE_MODEL || 'stability-ai/stable-diffusion']
    },
    capabilities: ['text', 'image'],
    maxTokens: 4096,
    costPerToken: 0,
    isLocal: true
  },
  
  [PROVIDERS.ZAI]: {
    name: 'Z.AI GLM-4.6',
    baseUrl: process.env.ZAI_BASE_URL || 'https://api.z.ai/api/paas/v4',
    apiKey: process.env.ZAI_API_KEY,
    models: {
      text: ['glm-4.6', 'glm-4.6-thinking', 'glm-4.6-streaming']
    },
    capabilities: ['text', 'reasoning', 'tool_use', 'long_context'],
    maxTokens: 200000,
    costPerToken: 0.00002,
    features: {
      thinkingMode: true,
      streaming: true,
      toolUse: true,
      longContext: true
    }
  }
};

export const getProviderConfig = (provider) => {
  const config = PROVIDER_CONFIGS[provider];
  if (!config) {
    throw new Error(`Unknown provider: ${provider}`);
  }
  if (!config.apiKey && !config.isLocal) {
    throw new Error(`API key not configured for provider: ${provider}`);
  }
  return config;
};

export const getAvailableProviders = () => {
  return Object.entries(PROVIDER_CONFIGS)
    .filter(([_, config]) => config.apiKey || config.isLocal)
    .map(([key, config]) => ({
      id: key,
      name: config.name,
      capabilities: config.capabilities,
      isLocal: config.isLocal || false
    }));
};

export const validateProvider = (provider, capability) => {
  const config = getProviderConfig(provider);
  if (!config.capabilities.includes(capability)) {
    throw new Error(`Provider ${provider} does not support ${capability}`);
  }
  return true;
};