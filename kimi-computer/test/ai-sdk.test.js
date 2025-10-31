// test/ai-sdk.test.js
import { generateContent, streamContent } from '../src/services/contentGenerator.js';
import { getActiveProvider } from '../src/config/providers.js';

describe('Vercel AI SDK Integration', () => {
  test('generate content with Mistral local', async () => {
    const content = await generateContent('Write a short test message');
    expect(content).toBeTruthy();
    expect(content.length).toBeGreaterThan(0);
  });

  test('streaming content generation', async () => {
    const chunks = [];
    for await (const chunk of streamContent('Test streaming')) {
      chunks.push(chunk);
    }
    expect(chunks.length).toBeGreaterThan(0);
    const fullContent = chunks.join('');
    expect(fullContent.length).toBeGreaterThan(0);
  });

  test('provider availability check', () => {
    const provider = getActiveProvider();
    expect(provider).toBeTruthy();
  });
});
