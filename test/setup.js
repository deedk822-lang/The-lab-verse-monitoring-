/* eslint-env jest */
import { jest } from '@jest/globals';

// Only silence logs in CI environment
if (process.env.CI === 'true') {
  global.console = {
    ...console,
    log: () => {}, // Silent but functional
    debug: () => {},
    info: () => {}
    // Keep warn and error for debugging
  };
}

// Set reasonable timeout (30s, not 90s)
jest.setTimeout(30000);

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});
