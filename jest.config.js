export default {
  testEnvironment: 'node',
  testTimeout: 90000, // 90 second timeout for network-heavy tests
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
  transformIgnorePatterns: [
    '/node_modules/(?!@automattic/mcp-wpcom-remote).+\\.js$',
  ],
  globals: {
    'ts-jest': {
      useESM: true
    }
  },
  testMatch: ['**/test/**/*.test.js'],
  modulePathIgnorePatterns: [
    '<rootDir>/scout-monetization/'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/content-creator-ai/',
    '/kimi-computer/',
    '/lapverse-ai-brain-trust/',
    '/lapverse-alpha/',
    '/lapverse-core/',
    '/src/routes/test.js',
    '/dist/',
    '/build/'
  ],
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/index.js',
    '!src/server.js'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'html'],
  verbose: true
};