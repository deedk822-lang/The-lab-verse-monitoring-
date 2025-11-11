// src/providers/parallelProvider.js
// Parallel web-search MCP integration with Groq inference

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
 * Generate content with real-time web search via Parallel MCP
 * Combines Groq's fast inference with Parallel's web search capabilities
 * 
 * @param {Object} options - Generation options
 * @param {Array} options.messages - Array of message objects
 * @param {string} options.model - Model to use (default: llama-3.1-70b-versatile)
 * @param {number} options.temperature - Temperature for generation (default: 0.1)
 * @param {number} options.max_tokens - Maximum tokens to generate (default: 1024)
 * @returns {Promise<string>} Search-augmented answer
 */
export async function generateWithParallelSearch({
  messages,
  model = 'llama-3.1-70b-versatile',
  temperature = 0.1,
  max_tokens = 1024
}) {
  if (!process.env.PARALLEL_API_KEY) {
    throw new Error('PARALLEL_API_KEY environment variable is not set');
  }

  try {
    const groq = getGroqClient();
    
    // Configure Parallel MCP tool for real-time web search
    const tools = [{
      type: 'mcp',
      server_label: 'parallel_web_search',
      server_url: 'https://mcp.parallel.ai/v1beta/search_mcp/',
      headers: { 'x-api-key': process.env.PARALLEL_API_KEY },
      require_approval: 'never'
    }];

    const res = await groq.chat.completions.create({
      model,
      messages,
      tools,
      tool_choice: 'auto',
      temperature,
      max_tokens
    });

    // Groq returns the search-augmented answer in the normal message
    return res.choices[0]?.message?.content || '';
  } catch (error) {
    console.error('❌ Groq+Parallel generation failed:', error.message);
    throw new Error(`Groq+Parallel API error: ${error.message}`);
  }
}

/**
 * Simplified single-query interface for quick research
 * @param {string} query - Research query
 * @param {Object} options - Generation options
 * @returns {Promise<string>} Research results
 */
export async function research(query, options = {}) {
  const messages = [{ role: 'user', content: query }];
  return await generateWithParallelSearch({ 
    messages, 
    ...options 
  });
}

export default {
  generateWithParallelSearch,
  research
};
