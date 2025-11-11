import { generateOpenAI } from './openaiProvider.js';
import { generateGroq } from './groqProvider.js';
import { generateGemini } from './geminiProvider.js';
import { generatePerplexity } from './perplexityProvider.js';
import { httpReq, tokenCounter, errorCounter } from '../metrics.js';

const providers = [
{ name: 'OpenAI', fn: generateOpenAI, env: 'OPENAI_API_KEY' },
{ name: 'Groq', fn: generateGroq, env: 'GROQ_API_KEY' },
{ name: 'Gemini', fn: generateGemini, env: 'GEMINI_API_KEY' },
{ name: 'Perplexity', fn: generatePerplexity, env: 'PERPLEXITY_API_KEY' }
];

export async function multiProviderGenerate({ messages, model = 'gpt-4' }) {
let lastError;
for (const p of providers) {
if (!process.env[p.env]) continue;
try {
const end = httpReq.startTimer({ provider: p.name, model });
const text = await p.fn({ messages, model });
end({ status: 'success' });
tokenCounter.inc({ provider: p.name, model }, Math.ceil(text.length / 4));
return { provider: p.name, text };
} catch (e) {
lastError = e;
errorCounter.inc({ provider: p.name, code: e.status || 500 });
console.warn(`⚠️ Provider ${p.name} failed: ${e.message}`);
}
}
throw lastError || new Error('All providers exhausted');
}
