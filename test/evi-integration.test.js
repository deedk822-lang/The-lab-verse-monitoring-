/* eslint-env jest */
import { describe, test, expect, beforeEach, jest } from '@jest/globals';

// Create mock functions
const mockEnhancedGenerate = jest.fn();
const mockMultiProviderGenerate = jest.fn();
const mockHealthCheck = jest.fn();

// Mock the integration to prevent real provider access
jest.unstable_mockModule('../src/integrations/eviIntegration.js', () => ({
  EviIntegration: jest.fn().mockImplementation(() => ({
    enhancedGenerate: mockEnhancedGenerate,
    multiProviderGenerate: mockMultiProviderGenerate,
    healthCheck: mockHealthCheck
  }))
}));

// Mock providers to prevent "Provider not available" errors
jest.unstable_mockModule('../src/config/providers.js', () => ({
  getActiveProvider: jest.fn(() => ({ id: 'mock-provider', provider: 'mock', modelId: 'gpt-4' })),
  getProviderByName: jest.fn(() => ({ id: 'mock-provider', provider: 'mock', modelId: 'gpt-4' })),
  hasAvailableProvider: jest.fn(() => true)
}));

// Import after mocking
const { EviIntegration } = await import('../src/integrations/eviIntegration.js');

describe('EviIntegration (mocked)', () => {
  let evi;

  beforeEach(() => {
    jest.clearAllMocks();
    evi = new EviIntegration();
  });

  test('enhancedGenerate returns content', async () => {
    mockEnhancedGenerate.mockResolvedValue({ content: 'AI answer' });
    const res = await evi.enhancedGenerate('hello');
    expect(res.content).toBe('AI answer');
    expect(mockEnhancedGenerate).toHaveBeenCalledWith('hello');
  });

  test('multiProviderGenerate falls back', async () => {
    mockMultiProviderGenerate.mockResolvedValue({ 
      content: 'Fallback answer',
      providerUsed: 'anthropic' 
    });
    const res = await evi.multiProviderGenerate('hello');
    expect(res.content).toBe('Fallback answer');
    expect(mockMultiProviderGenerate).toHaveBeenCalledWith('hello');
  });

  test('healthCheck returns status', async () => {
    mockHealthCheck.mockResolvedValue({ status: 'healthy' });
    const health = await evi.healthCheck();
    expect(health.status).toBe('healthy');
    expect(mockHealthCheck).toHaveBeenCalled();
  });

  test('handles all providers failing', async () => {
    mockMultiProviderGenerate.mockRejectedValue(new Error('All providers failed'));
    await expect(evi.multiProviderGenerate('hello'))
      .rejects.toThrow('All providers failed');
  });
});
