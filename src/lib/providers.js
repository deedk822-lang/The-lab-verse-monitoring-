/*  Unified provider registry
 *  Each entry: baseURL, authHeader(), list(), priority, enabled(), costPer1k
 */
export const providers = {
  zai: {
    baseURL: 'https://api.z.ai/api/anthropic',
    authHeader: () => ({ 'x-api-key': process.env.ZAI_API_KEY }),
    list: () => ['glm-4.6', 'glm-4.5-air', 'glm-4.5'],
    priority: 1,
    enabled: () => !!process.env.ZAI_API_KEY,
    costPer1k: { input: 0.015, output: 0.03 },
  },
  groq: {
    baseURL: 'https://api.groq.com/openai/v1',
    authHeader: () => ({ authorization: `Bearer ${process.env.GROQ_API_KEY}` }),
    list: () => ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'gpt-oss-120b', 'gpt-oss-20b', 'groq/compound', 'groq/compound-mini'],
    priority: 2,
    enabled: () => !!process.env.GROQ_API_KEY,
    costPer1k: { input: 0.00059, output: 0.00079 },
  },
  mistral: {
    baseURL: 'https://api.mistral.ai/v1',
    authHeader: () => ({ authorization: `Bearer ${process.env.MISTRAL_API_KEY}` }),
    list: () => ['mistral-medium-latest', 'mistral-large-latest', 'open-mistral-nemo', 'pixtral-12b', 'mistral-embed'],
    priority: 3,
    enabled: () => !!process.env.MISTRAL_API_KEY,
    costPer1k: { input: 0.002, output: 0.006 },
  },
  openai: {
    baseURL: 'https://api.openai.com/v1',
    authHeader: () => ({ authorization: `Bearer ${process.env.OPENAI_API_KEY}` }),
    list: () => ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
    priority: 4,
    enabled: () => !!process.env.OPENAI_API_KEY,
    costPer1k: { input: 0.005, output: 0.015 },
  },
  anthropic: {
    baseURL: 'https://api.anthropic.com/v1',
    authHeader: () => ({ 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01' }),
    list: () => ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'],
    priority: 5,
    enabled: () => !!process.env.ANTHROPIC_API_KEY,
    costPer1k: { input: 0.003, output: 0.015 },
  },
  bria: {
    baseURL: 'https://api.bria.ai/v1',
    authHeader: () => ({ 'x-api-key': process.env.BRIA_API_KEY }),
    list: () => ['bria/text-to-image', 'bria/image-editing', 'bria/background-removal', 'bria/controlnet-recolor', 'bria/product-shot', 'bria/ads-generation'],
    priority: 6,
    enabled: () => !!process.env.BRIA_API_KEY,
    costPer1k: { input: 0.04, output: 0.08 },
  },
  unito: {
    baseURL: 'https://api.unito.io/v4',
    authHeader: () => ({ authorization: `Bearer ${process.env.UNITO_ACCESS_TOKEN}` }),
    list: () => ['unito-mcp'],
    priority: 99,
    enabled: () => !!process.env.UNITO_ACCESS_TOKEN,
  },
  socialpilot: {
    baseURL: 'https://api.socialpilot.com/v2',
    authHeader: () => ({ 'x-api-key': process.env.SOCIALPILOT_API_KEY, 'x-access-token': process.env.SOCIALPILOT_ACCESS_TOKEN }),
    list: () => ['socialpilot-mcp'],
    priority: 99,
    enabled: () => !!(process.env.SOCIALPILOT_API_KEY && process.env.SOCIALPILOT_ACCESS_TOKEN),
  },
  huggingface: {
    baseURL: 'https://huggingface.co/api',
    authHeader: () => ({ authorization: `Bearer ${process.env.HF_API_TOKEN}` }),
    list: () => ['hf-mcp'],
    priority: 99,
    enabled: () => !!process.env.HF_API_TOKEN,
  },
};

export function pickProvider(requestedModel, registry = providers) {
  const enabled = Object.entries(registry).filter(([, p]) => p.enabled()).sort(([, a], [, b]) => a.priority - b.priority);
  if (enabled.length === 0) return { provider: null, upstreamModel: null, meta: null };

  for (const [name, meta] of enabled) if (meta.list().includes(requestedModel)) return { provider: meta, upstreamModel: requestedModel, meta: { name, ...meta } };

  const familyMap = { glm: 'zai', gpt: 'openai', claude: 'anthropic', llama: 'groq', mistral: 'mistral', gemini: 'google' };
  for (const [prefix, key] of Object.entries(familyMap)) {
    if (requestedModel.startsWith(prefix)) {
      const meta = registry[key];
      if (meta?.enabled()) return { provider: meta, upstreamModel: meta.list()[0], meta: { name: key, ...meta } };
    }
  }
  const [name, meta] = enabled[0];
  return { provider: meta, upstreamModel: meta.list()[0], meta: { name, ...meta } };
}
