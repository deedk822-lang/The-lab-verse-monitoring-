// src/services/contentGenerator.js
import { streamText } from 'ai';
import { getActiveProvider } from '../config/providers.js';
import { logger } from '../utils/logger.js';

export async function generateContent(prompt, options = {}) {
  const model = getActiveProvider();

  if (!model) {
    throw new Error('No AI provider available. Check your .env configuration.');
  }

  try {
    logger.info('Generating content with AI provider:', {
      promptLength: prompt.length,
      maxTokens: options.maxTokens || 500
    });

    const { text: textPromise } = streamText({
      model,
      prompt,
      maxTokens: options.maxTokens || 500,
      temperature: options.temperature || 0.7,
    });

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('AI generation timed out')), options.timeout || 30000)
    );

    const result = await Promise.race([textPromise, timeoutPromise]);

    logger.info('Content generation completed:', {
      resultLength: result.length
    });

    return result;

  } catch (error) {
    logger.error('Content generation failed:', {
      error: error.message,
      provider: 'mistral-local'
    });
    throw new Error(`AI generation failed: ${error.message}`);
  }
}

export async function* streamContent(prompt, options = {}) {
  const model = getActiveProvider();

  if (!model) {
    throw new Error('No AI provider available. Check your .env configuration.');
  }

  try {
    logger.info('Starting streaming content generation');

    const { textStream } = streamText({
      model,
      prompt,
      maxTokens: options.maxTokens || 500,
      temperature: options.temperature || 0.7,
    });

    for await (const chunk of textStream) {
      yield chunk;
    }

    logger.info('Streaming content generation completed');

  } catch (error) {
    logger.error('Streaming generation failed:', error.message);
    throw new Error(`Streaming failed: ${error.message}`);
  }
}