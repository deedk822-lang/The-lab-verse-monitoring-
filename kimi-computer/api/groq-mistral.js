// api/groq-mistral.js
import { Groq } from 'groq-sdk';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

export default async function handler(req) {
  if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 });

  const { prompt, model = 'mixtral-8x7b-32768' } = await req.json();

  const chatCompletion = await groq.chat.completions.create({
    messages: [{ role: 'user', content: prompt }],
    model: model,
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 0.9,
  });

  return new Response(JSON.stringify({
    content: chatCompletion.choices[0]?.message?.content || '',
    tokens_used: chatCompletion.usage.total_tokens,
    model: model,
    latency_ms: chatCompletion.response_ms
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
