/*  OpenAI-compatible universal chat + MCP tool-calling
 *  POST  /api/gateway/v1/chat/completions
 *  curl  -H "Authorization: Bearer $KEY"  \
 *        -d '{"model":"glm-4.6","messages":[{"role":"user","content":"ping"}]}'  \
 *        https://<your-domain>/api/gateway/v1/chat/completions
 */
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { pickProvider } from '../../../../../src/lib/providers.js';
import { cost, telemetry } from '../../../../../src/lib/telemetry.js';

export const config = { runtime: 'edge', regions: ['iad1','fra1','hnd1'] };
const tracer = trace.getTracer('ai-gateway');

export default async function handler(req) {
  const span = tracer.startSpan('gateway.chat');
  const t0 = performance.now();

  try {
    if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 });
    const body = await req.json();
    const { messages, model = 'glm-4.6', stream = false, tools, tool_choice, max_tokens, temperature } = body;

    const isMCP = Array.isArray(tools) && tools.length > 0;
    const { provider, upstreamModel, meta } = pickProvider(model);
    if (!provider) return new Response('No provider available', { status: 503 });

    const payload = {
      model: upstreamModel,
      messages,
      stream,
      max_tokens: max_tokens ?? 4096,
      temperature: temperature ?? 0.7,
      tools: isMCP ? tools : undefined,
      tool_choice: isMCP ? tool_choice : undefined,
    };

    const headers = {
      'content-type': 'application/json',
      ...provider.authHeader(),
      ...telemetry.traceHeaders(span),
    };

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30_000);

    const upstreamRes = await fetch(`${provider.baseURL}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    }).finally(() => clearTimeout(timeout));

    const duration = performance.now() - t0;
    cost.record({
      provider: meta.name,
      model: upstreamModel,
      status: upstreamRes.status,
      duration,
      inputTokens: JSON.stringify(messages).length / 4,
      stream,
    });

    if (!upstreamRes.ok) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: `${upstreamRes.status}` });
      return new Response(await upstreamRes.text(), { status: upstreamRes.status });
    }

    if (stream) {
      const { readable, writable } = new TransformStream();
      upstreamRes.body.pipeTo(writable);
      return new Response(readable, {
        headers: {
          'content-type': 'text/event-stream',
          'x-gateway-provider': meta.name,
          'x-gateway-model': upstreamModel,
          'x-trace-id': span.spanContext().traceId,
        },
      });
    }

    const json = await upstreamRes.json();
    span.setStatus({ code: SpanStatusCode.OK });
    return new Response(JSON.stringify(json), {
      headers: {
        'content-type': 'application/json',
        'x-gateway-provider': meta.name,
        'x-gateway-model': upstreamModel,
        'x-trace-id': span.spanContext().traceId,
      },
    });
  } catch (err) {
    span.recordException(err);
    span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
    return new Response('Gateway error', { status: 500 });
  } finally {
    span.end();
  }
}
