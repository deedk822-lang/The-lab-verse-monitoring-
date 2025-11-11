/* eslint-env jest */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';

// Mock the providers module
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-provider', provider: 'mock', modelId: 'gpt-4' })),
  getProviderByName: jest.fn((name) => {
    if (name === 'openai' || name === 'anthropic') {
      return { id: 'mock-provider', provider: 'mock', modelId: name };
    }
    return null;
  }),
  hasAvailableProvider: jest.fn(() => true)
}));

// Mock the AI SDK
const mockStreamText = jest.fn();
jest.unstable_mockModule('ai', () => ({
  streamText: mockStreamText
}));

// Import after mocking
const { EviIntegration } = await import('../src/integrations/eviIntegration.js');

describe('EviIntegration (mocked)', () => {
  let evi;

  beforeEach(() => {
    jest.clearAllMocks();
    evi = new EviIntegration();
    
    // Default mock response
    mockStreamText.mockReturnValue({
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
    mockStreamText.mockReturnValue({
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

  test('multiProviderGenerate falls back on failure', async () => {
    const { getProviderByName } = await import('../src/config/providers.js');
    
    // First provider fails
    getProviderByName.mockReturnValueOnce(null);
    // Second provider succeeds
    getProviderByName.mockReturnValueOnce({ id: 'mock-anthropic', provider: 'anthropic' });
    
    mockStreamText.mockReturnValue({
      text: Promise.resolve('Fallback answer'),
      textStream: (async function* () {
        yield 'Fallback answer';
      })()
    });

    const res = await evi.multiProviderGenerate('hello', {
      providers: ['mistral-local', 'gpt-4']
    });
    
    expect(res).toBeDefined();
    expect(res.providerUsed).toBeDefined();
  });

  test('healthCheck returns status', async () => {
    mockStreamText.mockReturnValue({
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
    const { getProviderByName } = await import('../src/config/providers.js');
    
    // All providers fail
    getProviderByName.mockReturnValue(null);

    await expect(
      evi.multiProviderGenerate('hello', {
        providers: ['openai', 'anthropic']
      })
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
});
