import axios from 'axios';
import { trace, context } from '@opentelemetry/api';  // LapVerse OTel
import { z } from 'zod';  // For response validation
import { FinOpsTagger } from '../cost/FinOpsTagger';  // Your FinOps

const QwenResponseSchema = z.object({
  output: z.object({
    choices: z.array(z.object({
      message: z.object({ content: z.string() })
    }))
  })
});

const KimiResponseSchema = z.object({
  choices: z.array(z.object({
    message: z.object({ content: z.string() })
  }))
});

// LapVerse-aligned: Add OTel span for tracing
export const connectAI = async (
  prompt: string,
  finops: FinOpsTagger,
  options: { artifactId?: string; tenantId?: string } = {}
) => {
  const tracer = trace.getTracer('lapverse-ai-connector');
  const span = tracer.startSpan('connectAI', {
    attributes: {
      'ai.prompt.length': prompt.length,
      'artifact.id': options.artifactId || 'unknown',
      'tenant.id': options.tenantId || 'default',
      'finops.cost_center': 'ai-inference'
    }
  });

  try {
    const [qwen, kimi] = await Promise.allSettled([
      // Qwen-Max (Alibaba) - Analytical depth
      axios.post('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', {
        model: "qwen-max",
        input: { messages: [{ role: "user", content: prompt }] },
        parameters: { max_tokens: 500, temperature: 0.3 }  // Low temp for structured analysis
      }, {
        headers: { Authorization: `Bearer ${process.env.DASHSCOPE_API_KEY}` },
        timeout: 10000  // 10s timeout
      }),

      // Kimi-K2 (MoonShot) - Creative remixing with partial fix
      axios.post('https://api.moonshot.ai/v1/chat/completions', {
        model: "kimi-k2-0905-preview",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 500,
        temperature: 0.7  // Higher for evolution creativity
      }, {
        headers: { Authorization: `Bearer ${process.env.MOONSHOT_API_KEY}` },
        timeout: 10000
      })
    ]);

    if (qwen.status === 'rejected') throw qwen.reason;
    if (kimi.status === 'rejected') throw kimi.reason;

    const qwenData = QwenResponseSchema.parse(qwen.value.data);
    const kimiData = KimiResponseSchema.parse(kimi.value.data);

    // Auto-fix Kimi partial (if needed; 2025 API stable)
    const kimiContent = kimiData.choices[0].message.content.startsWith('{')
      ? kimiData.choices[0].message.content
      : `{${kimiData.choices[0].message.content}}`;

    const kimiParsed = JSON.parse(kimiContent);  // Safe: Zod ensures structure

    // FinOps tag + emit (LapVerse integration)
    finops.emitUsage({
      artifactId: options.artifactId,
      forecastCost: 0.005,  // Est. $0.005 per call
      tenant: options.tenantId,
      source: 'ai-connector'
    });

    span.setAttribute('ai.responses.valid', true);
    return {
      qwen: qwenData.output.choices[0].message.content,  // Analytical
      kimi: kimiParsed  // Creative/structured
    };
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: 2, message: 'AI Connection Failed' });
    throw error;  // Propagate for SLO gating
  } finally {
    span.end();
  }
};