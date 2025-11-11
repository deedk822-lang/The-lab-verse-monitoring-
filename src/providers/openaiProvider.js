import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function generateOpenAI({
  model = 'gpt-4',
  messages,
  temperature = 0.7,
  max_tokens = 1024
}) {
  const res = await openai.chat.completions.create({
    model,
    messages,
    temperature,
    max_tokens
  });
  return res.choices[0]?.message?.content || '';
}
