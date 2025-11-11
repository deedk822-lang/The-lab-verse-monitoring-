// Jest setup file for test configuration
import dotenv from 'dotenv';
import { jest } from '@jest/globals';

// Load environment variables from .env.test or .env
dotenv.config({ path: '.env.test' });
dotenv.config({ path: '.env' });

// Set test environment variables
process.env.NODE_ENV = 'test';

// Suppress console logs during tests (unless explicitly needed)
// Comment these out if you need to debug tests
// global.console = {
//   ...console,
//   log: jest.fn(),
//   debug: jest.fn(),
//   info: jest.fn(),
//   warn: jest.fn(),
// };

// Configure default test timeouts for specific test patterns
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
});

// Global test utilities
global.delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Mock external services if no API keys are present
if (!process.env.OPENAI_API_KEY &&
    !process.env.ANTHROPIC_API_KEY &&
    !process.env.PERPLEXITY_API_KEY &&
    !process.env.GOOGLE_GENERATIVE_AI_API_KEY) {
  console.log('⚠️  No API keys found - tests will use mock responses');
}
