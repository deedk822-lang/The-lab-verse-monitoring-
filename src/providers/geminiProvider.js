import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

function convertMessagesToGemini(messages) {
  const geminiMessages = [];
  let currentMessage;

  for (const message of messages) {
    if (message.role === 'user') {
      if (currentMessage) {
        geminiMessages.push(currentMessage);
      }
      currentMessage = { role: 'user', parts: [{ text: message.content }] };
    } else if (message.role === 'assistant') {
      if (!currentMessage) {
        // This case should not happen in a well-formed conversation
        continue;
      }
      currentMessage.role = 'model';
      currentMessage.parts.push({ text: message.content });
      geminiMessages.push(currentMessage);
      currentMessage = null;
    }
  }

  if (currentMessage) {
    geminiMessages.push(currentMessage);
  }

  return geminiMessages;
}

export async function generateGemini({
  model = 'gemini-1.5-flash',
  messages,
  temperature = 0.7,
  max_tokens = 1024
}) {
  const geminiModel = genAI.getGenerativeModel({ model });
  const result = await geminiModel.generateContent({
    contents: convertMessagesToGemini(messages),
    generationConfig: {
      temperature,
      maxOutputTokens: max_tokens
    }
  });

  const response = await result.response;
  return response.text() || '';
}
