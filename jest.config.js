export default {
  testEnvironment: 'node',
  testTimeout: 30000,
  maxWorkers: '50%',
  cache: true,
  cacheDirectory: '.jest-cache',
  
  // Setup file
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  
  // Ignore patterns
  modulePathIgnorePatterns: [
    '<rootDir>/scout-monetization/',
    '<rootDir>/.jest-cache/',
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/build/'
  ],
  
  // Test match patterns
  testMatch: [
    '**/test/**/*.test.js',
    '**/test/**/*.test.ts',
    '**/tests/**/*.test.ts',
    '!**/test/**/*.integration.test.js'
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.js',
    'workflows/**/*.ts',
    '!src/**/*.test.js',
    '!src/**/__tests__/**',
    '!src/**/*.config.js'
  ],
  
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 65,
      lines: 70,
      statements: 70
    }
  },
  
  // Better error reporting
  verbose: true,
  detectOpenHandles: true,
  forceExit: true,
  
  // Transform configuration
  "extensionsToTreatAsEsm": [".ts"],
  transform: {
    '^.+\\.ts?$': [
      'ts-jest',
      {
        useESM: true,
      },
    ],
  },
  moduleNameMapper: {
    '^kimi-computer/(.*)$': '<rootDir>/kimi-computer/$1',
    '^workflow$': '<rootDir>/node_modules/workflow'
  },
  transformIgnorePatterns: [
    'node_modules/(?!(.pnpm|@workflow/core)/)',
  ],
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ]
};
