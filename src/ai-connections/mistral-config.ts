// src/ai-connections/mistral-config.ts

export const modelConfig = {
    // Primary Models (Mistral)
    visionary: "mistral-large-latest",
    operator: "codestral-latest",
    auditor: "mistral-large-latest", // Using large for deep reasoning
    challenger: "mistral-small-latest",

    // Fact-Checking Judges
    factChecker1: "gemini-pro",
    factChecker2: "llama3-70b-8192", // Groq
    factChecker3: "claude-3-opus-20240229", // Anthropic

    // Fallback Model
    fallback: "glm-4",
};

export const providerEndpoints = {
    mistral: "https://api.mistral.ai/v1/chat/completions",
    google: "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
    groq: "https://api.groq.com/openai/v1/chat/completions",
    anthropic: "https://api.anthropic.com/v1/messages",
    glm: process.env.GLM_API_ENDPOINT || "https://open.bigmodel.cn/api/paas/v4/chat/completions",
};
