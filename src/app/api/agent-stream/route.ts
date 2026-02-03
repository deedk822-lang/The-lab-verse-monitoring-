import { NextRequest } from 'next/server';
import OpenAI from 'openai';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const kimi = new OpenAI({
  apiKey: process.env.KIMI_API_KEY,
  baseURL: 'https://api.moonshot.cn/v1',
});

const emitEvent = (
  controller: ReadableStreamDefaultController,
  encoder: TextEncoder,
  payload: Record<string, unknown>,
) => {
  controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
};

const tryParseJson = (value: string): Record<string, unknown> | null => {
  try {
    return JSON.parse(value) as Record<string, unknown>;
  } catch {
    return null;
  }
};

export async function GET(req: NextRequest) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      if (!process.env.KIMI_API_KEY) {
        emitEvent(controller, encoder, {
          type: 'error',
          message: 'Missing KIMI_API_KEY',
        });
        controller.close();
        return;
      }

      emitEvent(controller, encoder, {
        type: 'connected',
        timestamp: new Date().toISOString(),
      });

      const heartbeat = setInterval(() => {
        emitEvent(controller, encoder, {
          type: 'heartbeat',
          timestamp: new Date().toISOString(),
        });
      }, 15000);

      try {
        const completion = await kimi.chat.completions.create({
          model: 'kimi-k2-0711',
          messages: [
            {
              role: 'system',
              content:
                'You are a Lab-Verse monitoring agent. Analyze the current Linear task "Add live agent stream implementation" and provide real-time thoughts on implementation strategy. Output JSON with: thought (string), confidence (number), action (string|null), linear_update (object|null).',
            },
            {
              role: 'user',
              content:
                'Begin monitoring and provide continuous stream of implementation thoughts for the live agent dashboard.',
            },
          ],
          stream: true,
          response_format: { type: 'json_object' },
          signal: req.signal,
        });

        let buffer = '';

        for await (const chunk of completion) {
          const content = chunk.choices[0]?.delta?.content ?? '';
          if (!content) {
            continue;
          }

          buffer += content;
          const maybeParsed = tryParseJson(buffer.trim());
          if (maybeParsed) {
            emitEvent(controller, encoder, {
              type: 'agent_thought',
              agent: 'kimi-k2-0711',
              timestamp: new Date().toISOString(),
              ...maybeParsed,
            });

            if (maybeParsed.linear_update) {
              emitEvent(controller, encoder, {
                type: 'linear_action',
                timestamp: new Date().toISOString(),
                linear_update: maybeParsed.linear_update,
              });
            }

            buffer = '';
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        emitEvent(controller, encoder, {
          type: 'error',
          message,
        });
      } finally {
        clearInterval(heartbeat);
      }

      controller.close();
    },
    cancel() {
      req.signal?.throwIfAborted?.();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
