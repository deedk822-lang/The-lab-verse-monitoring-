/* eslint-env jest */
import { jest } from '@jest/globals';

// Mock all dependencies BEFORE any imports
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-provider', provider: 'mock', modelId: 'gpt-4' })),
  getProviderByName: jest.fn((name) => {
    if (name === 'openai' || name === 'anthropic' || name === 'mistral-local' || name === 'gpt-4' || name === 'claude-sonnet') {
      return { id: 'mock-provider', provider: 'mock', modelId: name };
    }
    return null;
  }),
  hasAvailableProvider: jest.fn(() => true)
}));

jest.unstable_mockModule('ai', () => ({
  streamText: jest.fn()
}));

// Import after mocking
const { EviIntegration } = await import('../src/integrations/eviIntegration.js');
const { streamText } = await import('ai');
const { getProviderByName } = await import('../src/config/providers.js');

describe('EviIntegration (mocked)', () => {
  let evi;

  beforeEach(() => {
    jest.clearAllMocks();
    evi = new EviIntegration();

    // Default mock response
    streamText.mockReturnValue({
      text: Promise.resolve('AI answer'),
      textStream: (async function* () {
        yield 'AI answer';
      })()
    });
  });

  test('initialization', () => {
    expect(evi).toBeDefined();
    expect(evi.maxRetries).toBeDefined();
    expect(evi.timeout).toBe(30000);
  });

  test('enhancedGenerate returns content', async () => {
    streamText.mockReturnValue({
      text: Promise.resolve('AI answer'),
      textStream: (async function* () {
        yield 'AI answer';
      })()
    });

    const res = await evi.enhancedGenerate('hello');
    expect(res).toBeDefined();
    expect(res.content).toBeTruthy();
    expect(res.metadata).toBeDefined();
  });

  test('multiProviderGenerate uses first available provider', async () => {
    // All providers are available (mocked)
    getProviderByName.mockImplementation((name) => {
      return { id: `mock-${name}`, provider: 'mock', modelId: name };
    });

    streamText.mockReturnValue({
      text: Promise.resolve('Success answer'),
      textStream: (async function* () {
        yield 'Success answer';
      })()
    });

    const res = await evi.multiProviderGenerate('hello');

    expect(res).toBeDefined();
    expect(res.content).toBe('Success answer');
    expect(res.providerUsed).toBe('mistral-local'); // First in the list
    expect(res.fallbackAttempts).toBe(0);
  });

  test('multiProviderGenerate falls back on failure', async () => {
    // First provider fails, second succeeds
    getProviderByName
      .mockReturnValueOnce(null) // mistral-local fails
      .mockReturnValueOnce({ id: 'mock-gpt4', provider: 'mock', modelId: 'gpt-4' }); // gpt-4 succeeds

    streamText.mockReturnValue({
      text: Promise.resolve('Fallback answer'),
      textStream: (async function* () {
        yield 'Fallback answer';
      })()
    });

    const res = await evi.multiProviderGenerate('hello');

    expect(res).toBeDefined();
    expect(res.content).toBe('Fallback answer');
    expect(res.providerUsed).toBe('gpt-4');
    expect(res.fallbackAttempts).toBe(1); // Second provider
  });

  test('healthCheck returns status', async () => {
    streamText.mockReturnValue({
      text: Promise.resolve('OK'),
      textStream: (async function* () {
        yield 'OK';
      })()
    });

    const health = await evi.healthCheck();
    expect(health).toBeDefined();
    expect(health.status).toMatch(/healthy|degraded|unhealthy/i);
  });

  test('handles all providers failing', async () => {
    // All providers fail
    getProviderByName.mockReturnValue(null);

    await expect(
      evi.multiProviderGenerate('hello')
    ).rejects.toThrow(/All providers failed/i);
  });

  test('enhancePrompt adds context when enhance option is true', () => {
    const enhanced = evi.enhancePrompt('test prompt', {
      enhance: true,
      context: 'test context',
      tone: 'professional',
      format: 'markdown'
    });

    expect(enhanced).toContain('Context: test context');
    expect(enhanced).toContain('Tone: professional');
    expect(enhanced).toContain('Format: markdown');
    expect(enhanced).toContain('test prompt');
  });

  test('enhancePrompt returns original prompt when enhance is false', () => {
    const result = evi.enhancePrompt('test prompt', {
      enhance: false,
      context: 'should not appear'
    });

    expect(result).toBe('test prompt');
  });

  test('enhancedStream yields chunks with metadata', async () => {
    async function* mockStreamGen() {
      yield 'Chunk 1 ';
      yield 'Chunk 2 ';
      yield 'Chunk 3';
    }

    streamText.mockReturnValue({
      text: Promise.resolve('Chunk 1 Chunk 2 Chunk 3'),
      textStream: mockStreamGen()
    });

    const chunks = [];
    for await (const item of evi.enhancedStream('test')) {
      chunks.push(item);
    }

    // Should have 3 content chunks + 1 summary chunk
    expect(chunks.length).toBeGreaterThanOrEqual(3);
    
    // Check that content chunks have the expected structure
    const contentChunks = chunks.filter(c => c.chunk);
    expect(contentChunks.length).toBe(3);
    expect(contentChunks[0]).toHaveProperty('metadata');
    expect(contentChunks[0].metadata).toHaveProperty('chunkIndex');
    
    // Check summary chunk
    const summaryChunk = chunks.find(c => c.summary);
    expect(summaryChunk).toBeDefined();
    expect(summaryChunk.summary).toHaveProperty('completed', true);
  });
});
