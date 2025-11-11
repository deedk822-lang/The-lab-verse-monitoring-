/* eslint-env jest */
import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';

/* --------------  mocks -------------- */
const mockStreamText = jest.fn();

// Mock the providers module
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-model' })),
  getProviderByName: jest.fn((name) => {
    if (name === 'not-found') {
      return null;
    }
    return { id: 'mock-model' };
  }),
  hasAvailableProvider: jest.fn(() => true)
}));

// Mock the ai module
jest.unstable_mockModule('ai', () => ({
  streamText: mockStreamText
}));

// Import AFTER mocking
const { generateContent, streamContent } = await import('../src/services/contentGenerator.js');

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  jest.restoreAllMocks();
});
/* ------------------------------------ */

describe('Vercel AI SDK Integration (mocked)', () => {
  test('provider availability check', async () => {
    mockStreamText.mockReturnValue({
      text: Promise.resolve('ok'),
      textStream: (async function* () {
        yield 'ok';
      })()
    });

    const res = await generateContent('ping');
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

  test('error handling for missing prompt', async () => {
    mockStreamText.mockImplementation(() => {
      throw new Error('Prompt is required');
    });

    await expect(generateContent(''))
      .rejects.toThrow(/required|failed/i);
  }, 10000);

  test('timeout handling', async () => {
    // Mock a slow response that will timeout
    mockStreamText.mockReturnValue({
      text: new Promise((resolve) => setTimeout(() => resolve('too slow'), 5000)),
      textStream: (async function* () {
        await new Promise(resolve => setTimeout(resolve, 5000));
        yield 'too slow';
      })()
    });

    await expect(generateContent('trigger timeout', { timeout: 50 }))
      .rejects.toThrow(/timed out/i);
  });
});
