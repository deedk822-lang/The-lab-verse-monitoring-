// src/ai-connections/mistral-config.ts

export const mistralModels = {
  // Visionary Judge
  "pixoral-12b": {
    provider: "mistral",
    model: "pixoral-12b-2409",
    type: "multimodal",
  },
  // Operator Judge
  codestral: {
    provider: "mistral",
    model: "codestral",
    type: "code",
  },
  // Auditor Judge
  "mixtral-8x22b": {
    provider: "mistral",
    model: "mixtral-8x22b-instruct",
    type: "reasoning",
  },
};

export const supportingModels = {
  // Arbiter & Challenger Judge
  claude: {
    provider: "anthropic",
    model: "claude-3-opus-20240229",
  },
  // Fact-Checker Judge #1
  gemini: {
    provider: "google",
    model: "gemini-pro",
  },
  // Fact-Checker Judge #2
  groq: {
    provider: "groq",
    model: "llama3-70b-8192",
  },
};

export const fallbackModel = {
  "glm-4": {
    provider: "glm",
    model: "glm-4",
  },
};
