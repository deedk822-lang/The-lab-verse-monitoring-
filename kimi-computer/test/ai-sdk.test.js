/* eslint-env jest */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';

// Mock the providers module
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-mistral-local', provider: 'mistral' })),
  getProviderByName: jest.fn((name) => {
    if (name === 'not-found') {
      return null;
    }
    return { id: 'mock-mistral-local', provider: 'mistral' };
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
const { getActiveProvider } = await import('../src/config/providers.js');

describe('Vercel AI SDK Integration (mocked)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('generate content with Mistral local', async () => {
    mockStreamText.mockReturnValue({
      text: Promise.resolve('This is a test message.'),
      textStream: (async function* () {
        yield 'This is a test message.';
      })()
    });

    const content = await generateContent('Write a short test message');
    expect(content).toBeTruthy();
    expect(content.length).toBeGreaterThan(0);
    expect(content).toBe('This is a test message.');
  });

  test('streaming content generation', async () => {
    async function* mockStreamGen() {
      yield 'Test ';
      yield 'streaming ';
      yield 'content';
    }

    mockStreamText.mockReturnValue({
      text: Promise.resolve('Test streaming content'),
      textStream: mockStreamGen()
    });

    const chunks = [];
    for await (const chunk of streamContent('Test streaming')) {
      chunks.push(chunk);
    }
    expect(chunks.length).toBeGreaterThan(0);
    const fullContent = chunks.join('');
    expect(fullContent.length).toBeGreaterThan(0);
    expect(fullContent).toBe('Test streaming content');
  });

  test('provider availability check', () => {
    const provider = getActiveProvider();
    expect(provider).toBeTruthy();
    expect(provider).toBeDefined();
  });

  test('timeout handling', async () => {
    // Mock a slow response that will timeout
    const timeouts = [];
    mockStreamText.mockReturnValue({
      text: new Promise((resolve) => {
        const id = setTimeout(() => resolve('too slow'), 5000);
        timeouts.push(id);
      }),
      textStream: (async function* () {
        await new Promise(resolve => {
          const id = setTimeout(resolve, 5000);
          timeouts.push(id);
        });
        yield 'too slow';
      })()
    });

    try {
      await expect(generateContent('test', { timeout: 100 }))
        .rejects.toThrow(/timed out/i);
    } finally {
      // Clean up any pending timeouts
      timeouts.forEach(id => clearTimeout(id));
    }
  });
});
