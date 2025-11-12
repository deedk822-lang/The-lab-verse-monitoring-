import Groq from 'groq-sdk';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

export async function generateGroq({
  model = 'llama-3.1-70b-versatile',
  messages,
  temperature = 0.7,
  max_tokens = 1024
}) {
  const res = await groq.chat.completions.create({
    model,
    messages,
    temperature,
    max_tokens
  });
  return res.choices[0]?.message?.content || '';
}
