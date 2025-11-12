// src/services/contentGenerator.js
import { streamText } from 'ai';
import { getActiveProvider, getProviderByName } from '../config/providers.js';

/**
 * Generate content using AI
 * @param {string} prompt - The prompt for content generation
 * @param {Object} options - Generation options
 * @param {number} options.maxTokens - Maximum tokens to generate
 * @param {number} options.temperature - Temperature for generation
 * @param {number} options.timeout - Request timeout in milliseconds
 * @param {string} options.provider - Specific provider name (optional)
 * @returns {Promise<string>} Generated content
 */
export async function generateContent(prompt, options = {}) {
  // Get the AI model
  let model;
  if (options.provider) {
    model = getProviderByName(options.provider);
    if (!model) {
      throw new Error(`Provider ${options.provider} not available`);
    }
  } else {
    model = getActiveProvider();
  }

  if (!model) {
    throw new Error('No AI provider available. Please configure at least one provider.');
  }

  try {
    // streamText returns an object with promises
    const result = streamText({
      model,
      prompt,
      maxTokens: options.maxTokens || 500,
      temperature: options.temperature || 0.7
    });

    // Create timeout promise with cleanup
    let timeoutId;
    const timeoutPromise = new Promise((_, reject) => {
      timeoutId = setTimeout(() => reject(new Error('Request timed out')), options.timeout || 30000);
    });

    // Race between content generation and timeout
    try {
      const text = await Promise.race([result.text, timeoutPromise]);
      clearTimeout(timeoutId);
      return text;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }

  } catch (error) {
    console.error('❌ Content generation failed:', error.message);
    throw new Error(`Content generation failed: ${error.message}`);
  }
}

/**
 * Stream content generation for real-time responses
 * @param {string} prompt - The prompt for content generation
 * @param {Object} options - Generation options
 * @returns {AsyncGenerator} Stream of content chunks
 */
export async function* streamContent(prompt, options = {}) {
  const model = options.provider ?
    getProviderByName(options.provider) :
    getActiveProvider();

  if (!model) {
    throw new Error('No AI provider available');
  }

  try {
    const { textStream } = streamText({
      model,
      prompt,
      maxTokens: options.maxTokens || 500,
      temperature: options.temperature || 0.7
    });

    for await (const chunk of textStream) {
      yield chunk;
    }

  } catch (error) {
    console.error('❌ Streaming failed:', error.message);
    throw new Error(`Streaming failed: ${error.message}`);
  }
}

export default {
  generateContent,
  streamContent
};
