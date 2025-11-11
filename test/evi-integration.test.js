/* eslint-env jest */
import { describe, test, expect, jest } from '@jest/globals';

const mockEnhanced = jest.fn();
const mockMulti = jest.fn();
const mockHealth = jest.fn();

jest.unstable_mockModule('../src/integrations/eviIntegration.js', () => ({
  EviIntegration: {
    getInstance: () => ({
      enhancedGenerate: mockEnhanced,
      multiProviderGenerate: mockMulti,
      healthCheck: mockHealth
    })
  }
}));

// Import AFTER mocking
const { EviIntegration } = await import('../src/integrations/eviIntegration.js');
const evi = EviIntegration.getInstance();

describe('EviIntegration (unit)', () => {
  beforeEach(() => jest.clearAllMocks());

  test('enhancedGenerate returns content', async () => {
    mockEnhanced.mockResolvedValue({
      content: 'AI answer',
      metadata: { tokens: 10 }
    });
    const res = await evi.enhancedGenerate('hello');
    expect(res.content).toBe('AI answer');
  });

  test('multiProviderGenerate falls back', async () => {
    mockMulti.mockResolvedValue({
      content: 'Fallback answer',
      metadata: { provider: 'claude' }
    });
    const res = await evi.multiProviderGenerate('hello');
    expect(res.content).toBe('Fallback answer');
  });

  test('healthCheck returns status', async () => {
    mockHealth.mockResolvedValue({
      status: 'healthy',
      providers: [{ name: 'openai', status: 'healthy' }]
    });
    const health = await evi.healthCheck();
    expect(health.status).toBe('healthy');
  });
});
