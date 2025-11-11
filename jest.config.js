export default {
 cursor/create-ci-performance-dashboard-8ca4
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

  testTimeout: 30000,          // 30s reasonable timeout
  maxWorkers: '50%',           // Parallel execution
  cache: true,
  cacheDirectory: '.jest-cache',
  
  // Setup file
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  
  // Ignore patterns
 main
  modulePathIgnorePatterns: [
    '<rootDir>/scout-monetization/',
    '<rootDir>/.jest-cache/',
    '<rootDir>/node_modules/'
  ],
  
  // Test match patterns
  testMatch: [
    '**/test/**/*.test.js'
  ],
  
 cursor/create-ci-performance-dashboard-8ca4
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  

 main
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/**/__tests__/**'
  ],
 cursor/create-ci-performance-dashboard-8ca4
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
 main
};
