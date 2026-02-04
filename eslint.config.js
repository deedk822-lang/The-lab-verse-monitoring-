import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';

export default [
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/.next/**',
      '**/coverage/**',
      '**/.cache/**',
      'api/**',
      'assets/**',
      'cognitive-swarm/**',
      'config/**',
      'content-creator-ai/**',
      'deal-hunter/**',
      'docs/**',
      'kimi-computer/**',
      'lab_verse/**',
      'lapverse-ai-brain-trust/**',
      'lapverse-alpha/**',
      'lapverse-core/**',
      'mcp-server/**',
      'monitoring/**',
      'nginx/**',
      'openapi/**',
      'quantumguard-v2/**',
      'scout-monetization/**',
      'scripts/**',
      'test/**',
      'tests/**',
      'utils/**',
      'workflows/**',
      "**/Script's/**",
      '**/Re run validation script/**',
      '**/Action (ci) snippet/**',
      '**/srcmetrics.js../**',
      '**/Production ready/**',
      '**/Untitled File**'
    ]
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,mjs,cjs}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      }
    },
    plugins: {
      react,
      'react-hooks': reactHooks
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'warn',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
    },
    settings: {
      react: {
        version: 'detect'
      }
    }
  },
  prettier
];
