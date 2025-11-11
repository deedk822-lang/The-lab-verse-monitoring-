/* eslint-env jest */
import { jest } from '@jest/globals';

// Silence console logs during tests unless they fail
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Increase timeout for network-heavy suites
jest.setTimeout(90000);
