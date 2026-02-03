export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  let intervalId: ReturnType<typeof setInterval> | null = null;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  const encoder = new TextEncoder();

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      let index = 0;

      intervalId = setInterval(() => {
        const payload = {
          agent: 'Kimi K2.5',
          thought: `Analyzing subsystem ${++index}`,
          confidence: Math.random().toFixed(2),
        };

        controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
      }, 800);

      timeoutId = setTimeout(() => {
        if (intervalId) {
          clearInterval(intervalId);
        }
        controller.close();
      }, 60000);
    },
    cancel() {
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
