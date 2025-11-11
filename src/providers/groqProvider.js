// src/providers/groqProvider.js
import Groq from 'groq-sdk';

let groqClient = null;

/**
 * Get or initialize Groq client
 * @returns {Groq} Groq client instance
 */
function getGroqClient() {
  if (!process.env.GROQ_API_KEY) {
    throw new Error('GROQ_API_KEY environment variable is not set');
  }
  
  if (!groqClient) {
    groqClient = new Groq({ apiKey: process.env.GROQ_API_KEY });
  }
  
  return groqClient;
}

/**
 * Generate content using Groq's native SDK
 * @param {Object} options - Generation options
 * @param {string} options.model - Model to use (default: llama-3.1-70b-versatile)
 * @param {Array} options.messages - Array of message objects
 * @param {number} options.temperature - Temperature for generation (default: 0.7)
 * @param {number} options.max_tokens - Maximum tokens to generate (default: 1024)
 * @returns {Promise<string>} Generated content
 */
export async function generateGroq({ 
  model = 'llama-3.1-70b-versatile',
  messages,
  temperature = 0.7,
  max_tokens = 1024 
}) {
  try {
    const groq = getGroqClient();
    
    const res = await groq.chat.completions.create({
      model,
      messages,
      temperature,
      max_tokens
    });
    
    return res.choices[0]?.message?.content || '';
  } catch (error) {
    console.error('❌ Groq generation failed:', error.message);
    throw new Error(`Groq API error: ${error.message}`);
  }
}

/**
 * Stream content using Groq's native SDK
 * @param {Object} options - Generation options
 * @returns {AsyncGenerator} Stream of content chunks
 */
export async function* streamGroq({ 
  model = 'llama-3.1-70b-versatile',
  messages,
  temperature = 0.7,
  max_tokens = 1024 
}) {
  try {
    const groq = getGroqClient();
    
    const stream = await groq.chat.completions.create({
      model,
      messages,
      temperature,
      max_tokens,
      stream: true
    });
    
    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        yield content;
      }
    }
  } catch (error) {
    console.error('❌ Groq streaming failed:', error.message);
    throw new Error(`Groq streaming error: ${error.message}`);
  }
}

/**
 * Convert simple prompt to messages format
 * @param {string} prompt - Simple text prompt
 * @returns {Array} Messages array
 */
export function promptToMessages(prompt) {
  return [{ role: 'user', content: prompt }];
}

/**
 * Available Groq models
 */
export const GROQ_MODELS = {
  LLAMA_70B: 'llama-3.1-70b-versatile',
  LLAMA_8B: 'llama-3.1-8b-instant',
  MIXTRAL: 'mixtral-8x7b-32768',
  GEMMA: 'gemma2-9b-it'
};

export default {
  generateGroq,
  streamGroq,
  promptToMessages,
  GROQ_MODELS
};
