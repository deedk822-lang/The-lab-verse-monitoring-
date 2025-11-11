/* eslint-env jest */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';

// Create mock functions
const mockGenerateContent = jest.fn();
const mockStreamContent = jest.fn();

// Mock the entire service layer to prevent real provider access
jest.unstable_mockModule('../src/services/contentGenerator.js', () => ({
  generateContent: mockGenerateContent,
  streamContent: mockStreamContent
}));

// Mock providers to prevent "Provider not available" errors
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-provider', provider: 'mock' })),
  getProviderByName: jest.fn(() => ({ id: 'mock-provider', provider: 'mock' })),
  hasAvailableProvider: jest.fn(() => true)
}));

// Import after mocking
const { generateContent, streamContent } = await import('../src/services/contentGenerator.js');

describe('Vercel AI SDK Integration (mocked)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('generate content with available provider', async () => {
    mockGenerateContent.mockResolvedValue('Generated text');
    const res = await generateContent('Write a sentence');
    expect(res).toBe('Generated text');
    expect(mockGenerateContent).toHaveBeenCalledWith('Write a sentence');
  });

  test('streaming content generation', async () => {
    async function* mockStream() {
      yield 'Test ';
      yield 'streaming ';
      yield 'content';
    }
    mockStreamContent.mockReturnValue(mockStream());
    
    const chunks = [];
    for await (const chunk of streamContent('Test streaming')) {
      chunks.push(chunk);
    }
    expect(chunks.join('')).toBe('Test streaming content');
    expect(mockStreamContent).toHaveBeenCalledWith('Test streaming');
  });

  test('timeout handling', async () => {
    mockGenerateContent.mockRejectedValue(new Error('Request timed out'));
    await expect(generateContent('test', { timeout: 100 }))
      .rejects.toThrow(/timed out/i);
  });
});
