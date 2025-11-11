export default {
  testTimeout: 30000,          // 30s reasonable timeout
  maxWorkers: '50%',           // Parallel execution
  cache: true,
  cacheDirectory: '.jest-cache',
  
  // Setup file
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  
  // Ignore patterns
  modulePathIgnorePatterns: [
    '<rootDir>/scout-monetization/',
    '<rootDir>/.jest-cache/',
    '<rootDir>/node_modules/'
  ],
  
  // Test match patterns
  testMatch: [
    '**/test/**/*.test.js'
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/**/__tests__/**'
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
  forceExit: true // Prevent hanging tests
};
