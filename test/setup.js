/* eslint-env jest */

// Global test setup

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
 cursor/implement-stable-jest-mocking-for-test-isolation-d931

// Set reasonable timeout (30s, not 90s)
jest.setTimeout(30000);

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});

 main
