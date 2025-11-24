/** @type {import('ts-jest').JestConfigWithTsJest} */
export default {
  preset: 'ts-jest/presets/default-esm',
  testEnvironment: 'jsdom',
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { useESM: true, tsconfig: 'tsconfig.json' }],
  },
  transformIgnorePatterns: [
    'node_modules/(?!(node-fetch|@mswjs/interceptors|@workflow/core))',
  ],
  moduleNameMapper: {
    // Handle CSS imports (for component testing)
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',

    // Handle path aliases
    '^@/(.*)$': '<rootDir>/src/$1',

    // Existing mappings (preserve if necessary)
    '^@workflow/core$': '<rootDir>/workflows/core',
    '^../../src/gateway.js$': '<rootDir>/src/gateway.js',
    '^../services/ProviderFactory.js$': '<rootDir>/src/services/ProviderFactory.js',
    '^kimi-computer/src/services/contentGenerator.js$': '<rootDir>/kimi-computer/src/services/contentGenerator.js',
  },
  setupFilesAfterEnv: ['./test/setup.js'],
  setupFiles: ['./test/setup-nock.js'],
  testPathIgnorePatterns: ['<rootDir>/content-creator-ai/test.js'],
};
