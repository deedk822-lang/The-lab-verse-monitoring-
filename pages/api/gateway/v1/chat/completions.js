/**
 * OpenAI-compatible universal chat endpoint with MCP tool-calling
 *
 * POST /api/gateway/v1/chat/completions
 *
 * Example:
 * curl -X POST https://your-domain/api/gateway/v1/chat/completions \
 *   -H "Authorization: Bearer $API_KEY" \
 *   -H "Content-Type: application/json" \
 *   -d '{
 *     "model": "gpt-4",
 *     "messages": [{"role": "user", "content": "Hello!"}]
 *   }'
 */

import { trace, SpanStatusCode } from '@opentelemetry/api';
import { pickProvider } from '../../../../../src/lib/providers.js';
import { cost, telemetry } from '../../../../../src/lib/telemetry.js';

export const config = {
  runtime: 'edge',
  regions: ['iad1', 'fra1', 'hnd1']
};

const tracer = trace.getTracer('ai-gateway');

/**
 * Validate incoming request
 */
function validateRequest(body) {
  if (!body) {
    return { valid: false, error: 'Request body is required' };
  }

  if (!Array.isArray(body.messages) || body.messages.length === 0) {
    return { valid: false, error: 'messages array is required and must not be empty' };
  }

  // Validate message format
  for (const msg of body.messages) {
    if (!msg.role || !msg.content) {
      return { valid: false, error: 'Each message must have role and content' };
    }
    if (!['system', 'user', 'assistant', 'tool'].includes(msg.role)) {
      return { valid: false, error: `Invalid message role: ${msg.role}` };
    }
  }

  return { valid: true };
}

/**
 * Extract authentication token from request
 */
function getAuthToken(req) {
  const authHeader = req.headers.get('authorization');
  if (!authHeader) return null;

  // Support both "Bearer <token>" and "<token>"
  if (authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  return authHeader;
}

/**
 * Check if request is authorized
 */
function isAuthorized(token) {
  const validToken = process.env.GATEWAY_API_KEY || process.env.API_SECRET_KEY;

  // If no token is configured, allow all requests (development mode)
  if (!validToken) {
    console.warn('⚠️ No GATEWAY_API_KEY configured - authentication disabled');
    return true;
  }

  return token === validToken;
}

/**
 * Main handler
 */
export default async function handler(req) {
  const span = tracer.startSpan('gateway.chat.completions');
  const startTime = performance.now();

  try {
    // Method check
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed', allowed: ['POST'] }),
        { status: 405, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Authentication
    const token = getAuthToken(req);
    if (!isAuthorized(token)) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: 'Unauthorized' });
      return new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'Valid API key required in Authorization header'
        }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Parse and validate request
    let body;
    try {
      body = await req.json();
    } catch (error) {
      return new Response(
        JSON.stringify({ error: 'Invalid JSON', message: error.message }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const validation = validateRequest(body);
    if (!validation.valid) {
      return new Response(
        JSON.stringify({ error: 'Validation failed', message: validation.error }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Extract parameters
    const {
      messages,
      model = 'gpt-4',
      stream = false,
      tools,
      tool_choice,
      max_tokens = 4096,
      temperature = 0.7,
      top_p,
      frequency_penalty,
      presence_penalty,
      stop
    } = body;

    // Check if this is an MCP tool call
    const isMCP = Array.isArray(tools) && tools.length > 0;

    // Select provider
    const providerSelection = pickProvider(model);
    if (!providerSelection || !providerSelection.provider) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: 'No provider available' });
      return new Response(
        JSON.stringify({
          error: 'Provider not available',
          message: `No provider found for model: ${model}`,
          requested_model: model
        }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const { provider, upstreamModel, meta } = providerSelection;

    // Build upstream payload
    const payload = {
      model: upstreamModel,
      messages,
      stream,
      max_tokens,
      temperature
    };

    // Add optional parameters if provided
    if (top_p !== undefined) payload.top_p = top_p;
    if (frequency_penalty !== undefined) payload.frequency_penalty = frequency_penalty;
    if (presence_penalty !== undefined) payload.presence_penalty = presence_penalty;
    if (stop !== undefined) payload.stop = stop;

    // Add MCP tool parameters if present
    if (isMCP) {
      payload.tools = tools;
      if (tool_choice) payload.tool_choice = tool_choice;
    }

    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      ...provider.authHeader(),
      ...telemetry.traceHeaders(span)
    };

    // Create abort controller with timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout

    // Make upstream request
    let upstreamRes;
    try {
      upstreamRes = await fetch(`${provider.baseURL}/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal
      });
    } catch (error) {
      clearTimeout(timeout);

      if (error.name === 'AbortError') {
        span.setStatus({ code: SpanStatusCode.ERROR, message: 'Request timeout' });
        return new Response(
          JSON.stringify({
            error: 'Request timeout',
            message: 'Upstream provider took too long to respond'
          }),
          { status: 504, headers: { 'Content-Type': 'application/json' } }
        );
      }

      throw error;
    } finally {
      clearTimeout(timeout);
    }

    const duration = performance.now() - startTime;

    // Record cost metrics
    const inputTokens = JSON.stringify(messages).length / 4; // Rough estimate
    cost.record({
      provider: meta.name,
      model: upstreamModel,
      status: upstreamRes.status,
      duration,
      inputTokens,
      stream
    });

    // Handle error responses
    if (!upstreamRes.ok) {
      const errorText = await upstreamRes.text();
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: `Upstream ${upstreamRes.status}`
      });

      return new Response(
        JSON.stringify({
          error: 'Upstream provider error',
          status: upstreamRes.status,
          message: errorText,
          provider: meta.name,
          model: upstreamModel
        }),
        {
          status: upstreamRes.status,
          headers: {
            'Content-Type': 'application/json',
            'X-Gateway-Provider': meta.name,
            'X-Gateway-Model': upstreamModel,
            'X-Trace-Id': span.spanContext().traceId
          }
        }
      );
    }

    // Handle streaming response
    if (stream) {
      span.setAttribute('stream', true);

      const { readable, writable } = new TransformStream();
      upstreamRes.body.pipeTo(writable);

      return new Response(readable, {
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'X-Gateway-Provider': meta.name,
          'X-Gateway-Model': upstreamModel,
          'X-Trace-Id': span.spanContext().traceId,
          'X-Duration-Ms': Math.round(duration).toString()
        }
      });
    }

    // Handle JSON response
    const json = await upstreamRes.json();
    span.setStatus({ code: SpanStatusCode.OK });

    return new Response(JSON.stringify(json), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'X-Gateway-Provider': meta.name,
        'X-Gateway-Model': upstreamModel,
        'X-Trace-Id': span.spanContext().traceId,
        'X-Duration-Ms': Math.round(duration).toString()
      }
    });

  } catch (error) {
    // Log and record exception
    console.error('Gateway error:', error);
    span.recordException(error);
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message
    });

    return new Response(
      JSON.stringify({
        error: 'Internal gateway error',
        message: error.message,
        type: error.name
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'X-Trace-Id': span.spanContext().traceId
        }
      }
    );
  } finally {
    span.end();
  }
}
