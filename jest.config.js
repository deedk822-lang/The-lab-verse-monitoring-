export default {
  testTimeout: 30000, // 30s global timeout
  maxWorkers: '50%',
  cache: true,
  cacheDirectory: '.jest-cache',
  
  // ESM support
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
  transformIgnorePatterns: [
    '/node_modules/(?!@automattic/mcp-wpcom-remote).+\\.js$',
  ],
  
  // Test patterns
  testMatch: [
    '**/test/**/*.test.js'
  ],
  
  // Coverage
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/**/__tests__/**',
    '!src/index.js',
    '!src/server.js'
  ],
  
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 65,
      lines: 70,
      statements: 70
    }
  },
  
  // Module ignores
  modulePathIgnorePatterns: [
    '<rootDir>/scout-monetization/',
    '<rootDir>/.jest-cache/',
    '<rootDir>/node_modules/'
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
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'html'],
  verbose: true,
  testEnvironment: 'node'
};
