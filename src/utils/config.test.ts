import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { validateEnvironment, getEnvVar } from './config';

describe('Environment Config', () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('validateEnvironment', () => {
    it('should not throw an error if all required env vars are set', () => {
      process.env.NEXT_PUBLIC_API_ENDPOINT = 'https://api.example.com';
      process.env.NEXT_PUBLIC_EVENT_DATE = '2025-01-01';
      expect(() => validateEnvironment()).not.toThrow();
    });

    it('should throw an error if a required env var is missing', () => {
      delete process.env.NEXT_PUBLIC_API_ENDPOINT;
      expect(() => validateEnvironment()).toThrow('Configuration validation failed');
    });

    it('should throw an error when multiple vars are missing', () => {
        delete process.env.NEXT_PUBLIC_API_ENDPOINT;
        delete process.env.NEXT_PUBLIC_EVENT_DATE;
        expect(() => validateEnvironment()).toThrow('Configuration validation failed');
    });
  });

  describe('getEnvVar', () => {
    it('should return the value of an existing env var', () => {
      const testValue = 'test_value';
      process.env.MY_TEST_VAR = testValue;
      expect(getEnvVar('MY_TEST_VAR')).toBe(testValue);
    });

    it('should return the fallback value if the env var is not set', () => {
      const fallbackValue = 'fallback';
      expect(getEnvVar('NON_EXISTENT_VAR', fallbackValue)).toBe(fallbackValue);
    });

    it('should throw an error if the env var is not set and no fallback is provided', () => {
      expect(() => getEnvVar('NON_EXISTENT_VAR')).toThrow(
        'Environment variable NON_EXISTENT_VAR is required but not set'
      );
    });
  });
});
