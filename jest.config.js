/** @type {import('ts-jest').JestConfigWithTsJest} */
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
  transformIgnorePatterns: ['node_modules/(?!(node-fetch|@mswjs/interceptors)/)'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '^@workflow/core$': '<rootDir>/workflows/core',
    '^../../src/gateway.js$': '<rootDir>/src/gateway.js',
    '^../services/ProviderFactory.js$': '<rootDir>/src/services/ProviderFactory.js',
    '^kimi-computer/src/services/contentGenerator.js$': '<rootDir>/kimi-computer/src/services/contentGenerator.js',
  },
  setupFilesAfterEnv: ['./test/setup.js'],
  setupFiles: ['./test/setup-nock.js'],
  modulePaths: ['<rootDir>/src'],
  testPathIgnorePatterns: ['<rootDir>/content-creator-ai/test.js'],
};
