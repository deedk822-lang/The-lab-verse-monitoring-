// api/research.js
// Real-time web research endpoint using Groq+Parallel integration

import { research } from '../src/providers/parallelProvider.js';
import { multiProviderGenerate } from '../src/providers/multiProviderFallback.js';

/**
 * POST /api/research
 * 
 * Real-time web research endpoint powered by Groq inference + Parallel web search
 * 
 * Request body:
 * {
 *   "q": "Your research query",
 *   "model": "llama-3.1-70b-versatile" (optional),
 *   "temperature": 0.1 (optional),
 *   "use_fallback": true (optional - use multi-provider fallback chain)
 * }
 * 
 * Response:
 * {
 *   "success": true,
 *   "provider": "Groq+Parallel",
 *   "result": "Research results with sources...",
 *   "duration_ms": 2345
 * }
 * 
 * Examples:
 * - "What did Anthropic announce in the last 24 hours?"
 * - "Compare Tesla vs BYD stock performance today"
 * - "List the newest AI model releases announced this week"
 * - "Summarise today's news about SpaceX and list sources"
 */
export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      error: 'Method not allowed', 
      message: 'Use POST with {"q": "your query"}' 
    });
  }

  const { q, query, model, temperature, use_fallback } = req.body;
  const researchQuery = q || query;

  // Validate query
  if (!researchQuery || typeof researchQuery !== 'string') {
    return res.status(400).json({ 
      error: 'Bad request', 
      message: 'Missing or invalid "q" parameter in request body' 
    });
  }

  const startTime = Date.now();

  try {
    let result;
    let provider;

    if (use_fallback) {
      // Use multi-provider fallback chain (Groq+Parallel is first priority)
      console.log('🔍 Using multi-provider fallback for research...');
      const response = await multiProviderGenerate(researchQuery, {
        temperature: temperature || 0.1,
        max_tokens: 2048
      });
      result = response.text;
      provider = response.provider;
    } else {
      // Direct Groq+Parallel call (faster, requires both API keys)
      console.log('🔍 Using Groq+Parallel for research...');
      result = await research(researchQuery, {
        model: model || 'llama-3.1-70b-versatile',
        temperature: temperature || 0.1,
        max_tokens: 2048
      });
      provider = 'Groq+Parallel';
    }

    const duration = Date.now() - startTime;

    return res.status(200).json({
      success: true,
      provider,
      query: researchQuery,
      result,
      duration_ms: duration,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    const duration = Date.now() - startTime;
    
    console.error('❌ Research failed:', error.message);
    
    return res.status(500).json({
      success: false,
      error: error.message,
      query: researchQuery,
      duration_ms: duration,
      hint: 'Ensure GROQ_API_KEY and PARALLEL_API_KEY are set in environment variables'
    });
  }
}
