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
