import { sleep } from "@workflow/core";
import { generateContent } from "../kimi-computer/src/services/contentGenerator.js";

// A simple retry function to replace the one from the guide
async function retry<T>(fn: () => Promise<T>, options: { maxAttempts: number; backoff: string; }): Promise<T> {
  let attempts = 0;
  while (attempts < options.maxAttempts) {
    try {
      return await fn();
    } catch (err) {
      attempts++;
      if (attempts >= options.maxAttempts) {
        throw err;
      }
      const delay = options.backoff === "exponential" ? 2 ** attempts * 100 : 1000;
      await new Promise(res => setTimeout(res, delay));
    }
  }
  throw new Error("Retry failed");
}

// Placeholder for a function that processes analytics
async function processAnalytics(userId: string, result: any) {
  console.log(`Processing analytics for ${userId}...`);
  // This would involve sending data to an analytics service.
  return Promise.resolve();
}

export async function handleRequest(prompt: string, userId: string) {
  "use workflow";

  const result = await retry(
    () => generateContent(prompt, { provider: 'openai' }),
    { maxAttempts: 3, backoff: 'exponential' }
  );

  // Zero-cost analytics processing
  await sleep('1 hour');
  await processAnalytics(userId, result);

  return result;
}
