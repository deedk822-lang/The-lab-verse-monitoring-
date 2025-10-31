// src/services/contentGenerator.js
import { streamText } from 'ai';
import { getActiveProvider } from '../config/providers.js';

export async function generateContent(prompt, options = {}) {
  const model = getActiveProvider();

  if (!model) {
    throw new Error('No AI provider available');
  }

  try {
    // streamText synchronously returns an object containing the promise
    const { text: textPromise } = streamText({
      model,
      prompt,
      maxTokens: options.maxTokens || 500,
      temperature: options.temperature || 0.7,
    });

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Request timed out')), options.timeout || 10000)
    );

    return await Promise.race([textPromise, timeoutPromise]);

  } catch (error) {
    console.error('❌ Generation failed:', error.message);
    throw error;
  }
}

// Streaming variant for real-time responses
export async function* streamContent(prompt) {
  const model = getActiveProvider();

  if (!model) {
    throw new Error('No AI provider available');
  }

  const { textStream } = streamText({
    model,
    prompt,
  });

  for await (const chunk of textStream) {
    yield chunk;
  }
}
