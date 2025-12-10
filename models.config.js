export const MODEL_CATALOG = {
  // ** TIER 1: LocalAI-Compatible (Loadshedding-Proof) **
  'mistral-7b-instruct-v0.2-q4': {
    provider: 'LocalAI',
    endpoint: `${process.env.LOCALAI_ENDPOINT || 'http://your-public-localai-url'}/v1/chat/completions`,
    cost_per_1k_tokens: 0.0000, // Free, runs on Raspberry Pi
    capability: 6.5, // Out of 10
    specialization: 'content_generation',
    languages: ['en', 'af', 'nso', 'st'], // Sesotho support
    max_concurrent: 3, // Pi 4 can handle 3 sessions
    location: 'Sebokeng' // Physically hosted in Zone 14
  },

  'qwen2.5-coder-1.5b-q4': {
    provider: 'LocalAI',
    endpoint: `${process.env.LOCALAI_ENDPOINT || 'http://your-public-localai-url'}/v1/completions`,
    cost_per_1k_tokens: 0.0000,
    capability: 5.5,
    specialization: 'code_assistance',
    languages: ['en', 'af'],
    max_concurrent: 5,
    location: 'Vanderbijlpark' // For retrenched steelworkers learning Python
  },

  // ** TIER 2: Cloud-Based, Budget (Vercel Functions) **
  'mixtral-8x7b-together': {
    provider: 'Together AI',
    endpoint: 'https://api.together.xyz/v1/chat/completions',
    api_key_env: 'TOGETHER_API_KEY',
    cost_per_1k_tokens: 0.0006,
    capability: 8.0,
    specialization: 'job_matching',
    languages: ['en', 'af'],
    location: 'Vereeniging' // For small business automation
  },

  'llama-3.1-8b-groq': {
    provider: 'Groq',
    endpoint: 'https://api.groq.com/openai/v1/chat/completions',
    api_key_env: 'GROQ_API_KEY',
    cost_per_1k_tokens: 0.0008,
    capability: 7.5,
    specialization: 'semantic_search',
    languages: ['en'],
    location: 'Sasolburg' // Fast for industrial document search
  },

  'gemini-1.5-flash': {
    provider: 'Google',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
    api_key_env: 'GEMINI_API_KEY',
    cost_per_1k_tokens: 0.001,
    capability: 8.2,
    specialization: 'multimodal_analysis',
    languages: ['en', 'af', 'zu'],
    location: 'Meyerton'
  },

  // ** TIER 3: Premium (Requires Stable Power/Internet) **
  'gpt-4o-mini': {
    provider: 'OpenAI',
    endpoint: 'https://api.openai.com/v1/chat/completions',
    api_key_env: 'OPENAI_API_KEY',
    cost_per_1k_tokens: 0.012,
    capability: 8.5,
    specialization: 'executive_coaching',
    languages: ['en', 'af'],
    location: 'Three Rivers' // Only for fiber-connected clients
  },

  'claude-3.5-sonnet': {
    provider: 'Anthropic',
    endpoint: 'https://api.anthropic.com/v1/messages',
    api_key_env: 'ANTHROPIC_API_KEY',
    cost_per_1k_tokens: 0.024,
    capability: 9.2,
    specialization: 'compliance_analysis',
    languages: ['en'],
    location: 'Sharpeville' // For environmental justice document analysis
  },

  'cohere-embed-multilingual': {
    provider: 'Cohere',
    endpoint: 'https://api.cohere.ai/v1/embed',
    api_key_env: 'COHERE_API_KEY',
    cost_per_1k_tokens: 0.002,
    capability: 8.0,
    specialization: 'rag_embeddings',
    languages: ['en', 'af', 'st', 'nso', 'zu'],
    location: 'All' // For multilingual search across Vaal
  }
};
