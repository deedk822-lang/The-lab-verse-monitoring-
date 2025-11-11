/* eslint-env jest */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';

// Mock the providers module
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-model', provider: 'openai' })),
  getProviderByName: jest.fn((name) => {
    if (name === 'not-found') {
      return null;
    }
    return { id: 'mock-model', provider: 'openai' };
  }),
  hasAvailableProvider: jest.fn(() => true)
}));

// Mock the AI SDK
const mockStreamText = jest.fn();
jest.unstable_mockModule('ai', () => ({
  streamText: mockStreamText
}));

// Import after mocking
const { generateContent, streamContent } = await import('../src/services/contentGenerator.js');

describe('Vercel AI SDK Integration (mocked)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('provider availability check', async () => {
    mockStreamText.mockReturnValue({
      text: Promise.resolve('ok'),
      textStream: (async function* () {
        yield 'ok';
      })()
    });

    const res = await generateContent('ping');
    expect(res).toBeDefined();
    expect(res).toContain('ok');
  });

  test('generate content with available provider', async () => {
    mockStreamText.mockReturnValue({
      text: Promise.resolve('Generated text'),
      textStream: (async function* () {
        yield 'Generated text';
      })()
    });

    const res = await generateContent('Write a sentence');
    expect(res).toBe('Generated text');
  }, 10000);

  test('streaming content generation', async () => {
    async function* mockStreamGen() {
      yield 'Hello ';
      yield 'world';
    }

    mockStreamText.mockReturnValue({
      text: Promise.resolve('Hello world'),
      textStream: mockStreamGen()
    });

    const chunks = [];
    for await (const chunk of streamContent('Hello')) {
      chunks.push(chunk);
    }
    expect(chunks.join('')).toBe('Hello world');
  });

  test('error handling for invalid provider', async () => {
    const { getProviderByName } = await import('../src/config/providers.js');
    getProviderByName.mockReturnValueOnce(null);

    await expect(generateContent('test', { provider: 'not-found' }))
      .rejects.toThrow(/not.*available/i);
  }, 10000);

  test('error handling for API failure', async () => {
    mockStreamText.mockImplementation(() => {
      throw new Error('API Error: Server Error');
    });

    await expect(generateContent('test'))
      .rejects.toThrow(/failed|error/i);
  });

  test('timeout handling', async () => {
    // Mock a slow response that will timeout
    mockStreamText.mockReturnValue({
      text: new Promise((resolve) => setTimeout(() => resolve('too slow'), 5000)),
      textStream: (async function* () {
        await new Promise(resolve => setTimeout(resolve, 5000));
        yield 'too slow';
      })()
    });

    await expect(generateContent('test', { timeout: 100 }))
      .rejects.toThrow(/timed out/i);
  });

  test('respects maxTokens and temperature options', async () => {
    mockStreamText.mockReturnValue({
      text: Promise.resolve('response'),
      textStream: (async function* () {
        yield 'response';
      })()
    });

    await generateContent('test', { maxTokens: 100, temperature: 0.9 });

    expect(mockStreamText).toHaveBeenCalledWith(
      expect.objectContaining({
        maxTokens: 100,
        temperature: 0.9
      })
    );
  });
});
