import { trace, metrics, context } from '@opentelemetry/api';

const tracer = trace.getTracer('ai-provider', '1.0.0');
const meter = metrics.getMeter('ai-provider', '1.0.0');

// Create metrics
const requestCounter = meter.createCounter('ai_provider_requests_total', {
  description: 'Total number of AI provider requests',
  unit: '1',
});

const requestDuration = meter.createHistogram('ai_provider_request_duration_seconds', {
  description: 'AI provider request duration in seconds',
  unit: 's',
});

const errorCounter = meter.createCounter('ai_provider_errors_total', {
  description: 'Total number of AI provider errors',
  unit: '1',
});

const tokenCounter = meter.createCounter('ai_provider_tokens_total', {
  description: 'Total tokens consumed',
  unit: '1',
});

/**
 * Instrument an AI provider call with OpenTelemetry
 */
export async function instrumentedProviderCall({
  provider,
  model,
  messages,
  callFunction,
}) {
  // Start a span for this operation
  const span = tracer.startSpan('ai.generate', {
    attributes: {
      'ai.provider': provider,
      'ai.model': model,
      'ai.message_count': messages.length,
    },
  });

  const startTime = Date.now();

  try {
    // Execute the actual provider call within the span context
    const result = await context.with(
      trace.setSpan(context.active(), span),
      async () => await callFunction(),
    );

    const duration = (Date.now() - startTime) / 1000;

    // Add result attributes to span
    span.setAttributes({
      'ai.response_length': result.text?.length || 0,
      'ai.tokens_used': result.tokens || 0,
    });

    // Record success metrics
    requestCounter.add(1, {
      provider,
      model,
      status: 'success',
    });

    requestDuration.record(duration, {
      provider,
      model,
    });

    if (result.tokens) {
      tokenCounter.add(result.tokens, {
        provider,
        model,
      });
    }

    // Mark span as successful
    span.setStatus({ code: 1 }); // SpanStatusCode.OK
    span.end();

    return result;

  } catch (error) {
    const duration = (Date.now() - startTime) / 1000;

    // Add error attributes to span
    span.setAttributes({
      'error.type': error.name,
      'error.message': error.message,
    });

    // Record error metrics
    errorCounter.add(1, {
      provider,
      model,
      error_type: error.name,
      error_code: error.status || 'unknown',
    });

    requestCounter.add(1, {
      provider,
      model,
      status: 'error',
    });

    requestDuration.record(duration, {
      provider,
      model,
    });

    // Mark span as failed
    span.setStatus({
      code: 2, // SpanStatusCode.ERROR
      message: error.message,
    });
    span.recordException(error);
    span.end();

    throw error;
  }
}

/**
 * Example usage with Groq provider
 */
export async function generateWithGroq({ messages, model = 'llama-3.1-70b-versatile' }) {
  return instrumentedProviderCall({
    provider: 'Groq',
    model,
    messages,
    callFunction: async () => {
      const Groq = (await import('groq-sdk')).default;
      const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

      const response = await groq.chat.completions.create({
        model,
        messages,
        temperature: 0.7,
        max_tokens: 1024,
      });

      return {
        text: response.choices[0]?.message?.content || '',
        tokens: response.usage?.total_tokens || 0,
      };
    },
  });
}

/**
 * Example usage with OpenAI provider
 */
export async function generateWithOpenAI({ messages, model = 'gpt-4' }) {
  return instrumentedProviderCall({
    provider: 'OpenAI',
    model,
    messages,
    callFunction: async () => {
      const OpenAI = (await import('openai')).default;
      const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

      const response = await openai.chat.completions.create({
        model,
        messages,
        temperature: 0.7,
        max_tokens: 1024,
      });

      return {
        text: response.choices[0]?.message?.content || '',
        tokens: response.usage?.total_tokens || 0,
      };
    },
  });
}

/**
 * Multi-provider fallback with instrumentation
 */
export async function multiProviderGenerateInstrumented({ messages, model = 'gpt-4' }) {
  const providers = [
    { name: 'OpenAI', fn: generateWithOpenAI, env: 'OPENAI_API_KEY' },
    { name: 'Groq', fn: generateWithGroq, env: 'GROQ_API_KEY' },
  ];

  const span = tracer.startSpan('ai.multi_provider_generate');

  let lastError;

  for (const provider of providers) {
    if (!process.env[provider.env]) {
      continue;
    }

    try {
      const result = await provider.fn({ messages, model });
      span.setAttributes({
        'ai.provider_used': provider.name,
        'ai.fallback_attempts': providers.indexOf(provider) + 1,
      });
      span.setStatus({ code: 1 });
      span.end();
      return { ...result, provider: provider.name };
    } catch (error) {
      lastError = error;
      console.warn(`⚠️  Provider ${provider.name} failed: ${error.message}`);
    }
  }

  span.setStatus({ code: 2, message: 'All providers failed' });
  span.recordException(lastError);
  span.end();

  throw lastError || new Error('All providers exhausted');
}
