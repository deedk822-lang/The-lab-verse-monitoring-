import OpenAI from 'openai';

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY,
  baseURL: 'https://api.perplexity.ai'
});

export async function generatePerplexity({
  model = 'llama-3-sonar-large-32k-online',
  messages,
  temperature = 0.7,
  max_tokens = 1024
}) {
  const res = await perplexity.chat.completions.create({
    model,
    messages,
    temperature,
    max_tokens
  });
  return res.choices[0]?.message?.content || '';
}
