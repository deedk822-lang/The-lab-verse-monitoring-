/**
 * Mistral AI Models Configuration
 * Based on the Final Blueprint for Autonomous Authority and Impact Engine
 *
 * Core Models:
 * - Pixtral-12B-2409: Vision + Language multimodal model
 * - Codestral: Code generation and analysis
 * - Mixtral-8x22B: Large-scale reasoning and generation
 */

export interface MistralModelConfig {
  name: string;
  apiEndpoint: string;
  apiKey: string;
  maxTokens: number;
  temperature: number;
  role: 'visionary' | 'operator' | 'auditor' | 'challenger';
}

export const MISTRAL_MODELS: Record<string, MistralModelConfig> = {
  PIXTRAL: {
    name: 'pixtral-12b-2409',
    apiEndpoint: process.env.MISTRAL_API_URL || 'https://api.mistral.ai/v1',
    apiKey: process.env.MISTRAL_API_KEY || '',
    maxTokens: 4096,
    temperature: 0.7,
    role: 'visionary'
  },
  CODESTRAL: {
    name: 'codestral-latest',
    apiEndpoint: process.env.MISTRAL_API_URL || 'https://api.mistral.ai/v1',
    apiKey: process.env.MISTRAL_API_KEY || '',
    maxTokens: 8192,
    temperature: 0.3,
    role: 'operator'
  },
  MIXTRAL: {
    name: 'mixtral-8x22b-instruct',
    apiEndpoint: process.env.MISTRAL_API_URL || 'https://api.mistral.ai/v1',
    apiKey: process.env.MISTRAL_API_KEY || '',
    maxTokens: 16384,
    temperature: 0.5,
    role: 'auditor'
  }
};

export const AI_PROVIDERS = {
  MISTRAL: 'mistral',
  OPENAI: 'openai',
  ANTHROPIC: 'anthropic',
  GEMINI: 'gemini',
  GROQ: 'groq',
  GLM: 'glm'
} as const;

export interface AIConnectionConfig {
  provider: typeof AI_PROVIDERS[keyof typeof AI_PROVIDERS];
  model: string;
  apiKey: string;
  apiEndpoint?: string;
  fallbackModel?: string;
}

/**
 * Multi-provider AI connection configuration
 * Supports fallback mechanisms for resilience
 */
export const AI_CONNECTIONS: Record<string, AIConnectionConfig> = {
  PRIMARY_GENERATOR: {
    provider: AI_PROVIDERS.MISTRAL,
    model: MISTRAL_MODELS.MIXTRAL.name,
    apiKey: process.env.MISTRAL_API_KEY || '',
    apiEndpoint: MISTRAL_MODELS.MIXTRAL.apiEndpoint,
    fallbackModel: 'glm-4'
  },
  VISION: {
    provider: AI_PROVIDERS.MISTRAL,
    model: MISTRAL_MODELS.PIXTRAL.name,
    apiKey: process.env.MISTRAL_API_KEY || '',
    apiEndpoint: MISTRAL_MODELS.PIXTRAL.apiEndpoint
  },
  CODE: {
    provider: AI_PROVIDERS.MISTRAL,
    model: MISTRAL_MODELS.CODESTRAL.name,
    apiKey: process.env.MISTRAL_API_KEY || '',
    apiEndpoint: MISTRAL_MODELS.CODESTRAL.apiEndpoint
  },
  CONSENSUS_ARBITER: {
    provider: AI_PROVIDERS.ANTHROPIC,
    model: 'claude-3-5-sonnet-20241022',
    apiKey: process.env.ANTHROPIC_API_KEY || ''
  },
  FACT_CHECK_JUDGE_1_VISIONARY: {
    provider: AI_PROVIDERS.GEMINI,
    model: 'gemini-2.0-flash-exp',
    apiKey: process.env.GEMINI_API_KEY || ''
  },
  FACT_CHECK_JUDGE_2_OPERATOR: {
    provider: AI_PROVIDERS.GROQ,
    model: 'llama-3.3-70b-versatile',
    apiKey: process.env.GROQ_API_KEY || ''
  },
  FACT_CHECK_JUDGE_3_AUDITOR: {
    provider: AI_PROVIDERS.MISTRAL,
    model: MISTRAL_MODELS.MIXTRAL.name,
    apiKey: process.env.MISTRAL_API_KEY || '',
    apiEndpoint: MISTRAL_MODELS.MIXTRAL.apiEndpoint
  }
};

/**
 * Judge roles for the Multi-Judge Fact-Checking Protocol
 */
export const JUDGE_ROLES = {
  VISIONARY: {
    name: 'Visionary Judge',
    model: MISTRAL_MODELS.PIXTRAL,
    systemPrompt: 'You are a Visionary Judge. Evaluate claims with forward-thinking analysis, considering future implications and innovative perspectives. Provide evidence-based verdicts.'
  },
  OPERATOR: {
    name: 'Operator Judge',
    model: MISTRAL_MODELS.CODESTRAL,
    systemPrompt: 'You are an Operator Judge. Evaluate claims with practical, implementation-focused analysis. Focus on feasibility, technical accuracy, and operational viability. Provide evidence-based verdicts.'
  },
  AUDITOR: {
    name: 'Auditor Judge',
    model: MISTRAL_MODELS.MIXTRAL,
    systemPrompt: 'You are an Auditor Judge. Evaluate claims with rigorous scrutiny, focusing on accuracy, compliance, and risk assessment. Provide evidence-based verdicts with detailed citations.'
  },
  CHALLENGER: {
    name: 'Challenger Judge',
    model: AI_CONNECTIONS.CONSENSUS_ARBITER,
    systemPrompt: 'You are a Challenger Judge. Critically evaluate claims by identifying weaknesses, contradictions, and alternative perspectives. Provide evidence-based verdicts that challenge assumptions.'
  }
} as const;

export default {
  MISTRAL_MODELS,
  AI_PROVIDERS,
  AI_CONNECTIONS,
  JUDGE_ROLES
};
