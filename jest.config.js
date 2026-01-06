/** @type {import('jest').Config} */
const config = {
  rootDir: '.',
  testEnvironment: 'jsdom',
  
  // Match all test files across the repository
  testMatch: [
    '<rootDir>/**/*.(test|spec).{js,jsx,ts,tsx}',
    '<rootDir>/test/**/*.test.{js,ts}',
    '<rootDir>/tests/**/*.test.{js,ts}',
    '<rootDir>/test-*.js'
  ],
  
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json', 'node'],
  
  // Transform configuration for TypeScript and JavaScript
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true
      }
    }],
    '^.+\\.(js|jsx)$': ['babel-jest', { configFile: './babel.config.js' }]
  },
  
  // Transform ES modules in node_modules
  transformIgnorePatterns: [
    'node_modules/(?!(node-fetch|@mswjs/interceptors|fetch-blob|data-uri-to-buffer|formdata-polyfill)/)'
  ],
  
  // Module name mapping for aliases and CSS
  moduleNameMapper: {
    'msw/node': '<rootDir>/node_modules/msw/node/index.js',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@workflow/core$': '<rootDir>/workflows/core',
    '^../../src/gateway.js$': '<rootDir>/src/gateway.js',
    '^../services/ProviderFactory.js$': '<rootDir>/src/services/ProviderFactory.js',
    '^kimi-computer/src/services/contentGenerator.js$': '<rootDir>/kimi-computer/src/services/contentGenerator.js'
  },
  
  // Setup files
  setupFiles: ['<rootDir>/test/setup-nock.js'],
  setupFilesAfterEnv: ['<rootDir>/test/setup.js'],
  
  modulePaths: ['<rootDir>/src', '<rootDir>'],
  
  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '<rootDir>/.next/',
    '<rootDir>/dist/',
    '<rootDir>/content-creator-ai/test.js'
  ],
  
  // Coverage configuration (optional)
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!**/node_modules/**'
  ],
  
  // Error handling
  bail: false,
  verbose: true,
  
  // Timeout for tests
  testTimeout: 30000,
  
  // Clear mocks between tests
  clearMocks: true,
  restoreMocks: true
};

export default config;
