export default {
  testEnvironment: 'node',
  globals: {
    'ts-jest': {
      useESM: true
    }
  },
  testMatch: ['**/test/**/*.test.js', '**/?(*.)+(spec|test).js'],
  setupFilesAfterEnv: [],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/index.js',
    '!src/server.js'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'html'],
  testTimeout: 30000, // 30 second timeout for AI provider tests
  verbose: true
};