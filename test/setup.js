/* eslint-env jest */
import { jest } from '@jest/globals';

// Only silence logs in CI environment
if (process.env.CI === 'true') {
  const originalConsole = global.console;
  global.console = {
    ...originalConsole,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    // Keep error and warn for debugging
    error: originalConsole.error,
    warn: originalConsole.warn
  };
}

// Set reasonable default timeout
jest.setTimeout(30000);

// Global test utilities
global.testUtils = {
  wait: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  mockDate: (date) => {
    const mockDate = new Date(date);
    jest.spyOn(global, 'Date').mockImplementation(() => mockDate);
  }
};

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});
