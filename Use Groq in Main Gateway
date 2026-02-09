// pages/api/gateway/v1/chat/completions.js
if (req.body.model.startsWith('groq-')) {
  // Route to Groq instead of OpenAI
  const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
  return groq.chat.completions.create(req.body);
}
