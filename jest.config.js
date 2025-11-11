export default {
  testEnvironment: 'node',
  testTimeout: 90000, // 90 second timeout for network-heavy tests
  
  // Transform configuration
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
  
  // Test matching
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
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/index.js',
    '!src/server.js'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'html', 'json-summary', 'lcov'],
  
  // Coverage thresholds - enforce quality gates
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80
    }
  },
  
  // Performance and reporting
  verbose: true,
  detectOpenHandles: true,
  forceExit: false,
  
  // Reporters for rich output
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: './test-results',
      outputName: 'junit.xml',
      classNameTemplate: '{classname}',
      titleTemplate: '{title}',
      ancestorSeparator: ' › ',
      usePathForSuiteName: true
    }],
    ['jest-html-reporter', {
      pageTitle: 'Test Report',
      outputPath: './test-results/index.html',
      includeFailureMsg: true,
      includeConsoleLog: true,
      theme: 'darkTheme',
      sort: 'status'
    }]
  ],
  
  // Performance optimizations
  maxWorkers: '50%',
  bail: false,
  
  // Cache configuration
  cache: true,
  cacheDirectory: '/tmp/jest-cache'
};
