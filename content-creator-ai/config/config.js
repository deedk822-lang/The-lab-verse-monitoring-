require('dotenv').config();

const config = {
  server: {
    port: process.env.PORT || 3000,
    env: process.env.NODE_ENV || 'development',
    apiKey: process.env.API_KEY || 'default-api-key-change-me'
  },
  
  providers: {
    default: process.env.DEFAULT_PROVIDER || 'google',
    
    openai: {
      apiKey: process.env.OPENAI_API_KEY,
      enabled: !!process.env.OPENAI_API_KEY,
      models: {
        text: 'gpt-4-turbo-preview',
        vision: 'gpt-4-vision-preview',
        tts: 'tts-1'
      }
    },
    
    google: {
      apiKey: process.env.GOOGLE_API_KEY,
      enabled: !!process.env.GOOGLE_API_KEY,
      searchEngineId: process.env.GOOGLE_SEARCH_ENGINE_ID,
      mapsApiKey: process.env.GOOGLE_MAPS_API_KEY,
      models: {
        text: 'gemini-1.5-pro',
        vision: 'gemini-1.5-pro-vision',
        imagen: 'imagen-3.0',
        veo: 'veo-3.1'
      }
    },
    
    localai: {
      url: process.env.LOCALAI_URL || 'http://localhost:8080',
      enabled: process.env.LOCALAI_ENABLED === 'true',
      models: {
        text: 'llama-3.2-1b-instruct',
        vision: 'llava',
        tts: 'piper'
      }
    },
    
    zai: {
      apiKey: process.env.ZAI_API_KEY,
      enabled: !!process.env.ZAI_API_KEY,
      endpoint: process.env.ZAI_API_ENDPOINT || 'https://api.z.ai/api/paas/v4/chat/completions',
      model: process.env.ZAI_MODEL || 'glm-4.6',
      maxTokens: 200000
    },
    
    anthropic: {
      apiKey: process.env.ANTHROPIC_API_KEY,
      enabled: !!process.env.ANTHROPIC_API_KEY,
      models: {
        text: 'claude-3-opus-20240229'
      }
    },
    
    perplexity: {
      apiKey: process.env.PERPLEXITY_API_KEY,
      enabled: !!process.env.PERPLEXITY_API_KEY,
      models: {
        search: 'pplx-7b-online'
      }
    }
  },
  
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
    enabled: process.env.REDIS_ENABLED === 'true',
    ttl: 3600 // 1 hour default cache
  },
  
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 60000,
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100
  },
  
  costs: {
    trackCosts: process.env.TRACK_COSTS === 'true',
    pricing: {
      openai: {
        'gpt-4-turbo-preview': { input: 0.01, output: 0.03 }, // per 1K tokens
        'gpt-4-vision-preview': { input: 0.01, output: 0.03 },
        'tts-1': { perChar: 0.000015 }
      },
      google: {
        'gemini-1.5-pro': { input: 0.00125, output: 0.005 }, // per 1K tokens
        'imagen-3.0': { perImage: 0.04 },
        'veo-3.1': { perSecond: 0.10 }
      },
      zai: {
        'glm-4.6': { input: 0.0005, output: 0.0015 } // per 1K tokens (estimated)
      },
      localai: {
        default: { input: 0, output: 0 } // Free/self-hosted
      }
    }
  },
  
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    dir: 'logs'
  }
};

module.exports = config;
