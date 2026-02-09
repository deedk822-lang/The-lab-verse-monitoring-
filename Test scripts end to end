// test_local_mcp.js
import { config } from "dotenv";
import OpenAI from "openai";

config(); // loads .env

(async () => {
  // 1) Mistral (LocalAI)
  const mistral = new OpenAI({
    baseURL: process.env.MISTRAL_API_URL,
    apiKey: process.env.MISTRAL_API_KEY,
  });

  const r1 = await mistral.chat.completions.create({
    model: "hermes-2-pro-mistral",
    messages: [{ role: "user", content: "Write a one-line poem about clouds." }],
  });
  console.log("Mistral →", r1.choices[0].message.content.trim());

  // 2) Example: call a Groq/GPT provider that might route via MCP (optional)
  const groq = new OpenAI({
    baseURL: "https://api.groq.com/openai/v1",
    apiKey: process.env.GROQ_API_KEY,
  });

  const r2 = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: "How many rows are in the orders table?" }],
  });
  console.log("Groq/Claude→", r2.choices[0].message.content.trim());
})();
