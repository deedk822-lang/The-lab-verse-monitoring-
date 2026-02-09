# CI Testing Guide

## Overview

This project uses a professional multi-language test orchestration system that handles JavaScript/TypeScript (Jest) and Python (pytest) tests with robust error handling and graceful degradation.

## Quick Start

### Run All Tests Locally

```bash
# Run complete CI test suite
npm test

# Run only JavaScript/TypeScript tests
npm run test:js

# Run only Python tests
npm run test:py

# Run integration tests
npm run test:integration
```

## Architecture

### Test Orchestrator (`run-test-suite-ci.js`)

The main test runner that:
- Executes Jest and pytest in sequence
- Handles missing dependencies gracefully
- Provides detailed error reporting
- Exits with appropriate codes for CI

### Error Handling Features

#### 1. **Missing Dependencies**
- **Jest not found**: Fails with clear installation instructions
- **pytest not found**: Treats as skip (Python tests optional)
- **No tests found**: Passes (not an error)

#### 2. **Test Failures**
- Captures and displays failed test files
- Shows first 5 failures with details
- Provides summary with exit code 1

#### 3. **Exit Codes**
```
0 = All tests passed (some may be skipped)
1 = Test failures or critical errors
```

## Jest Configuration

### Test Patterns

Jest will find tests matching:
```
**/*.(test|spec).{js,jsx,ts,tsx}
test/**/*.test.{js,ts}
tests/**/*.test.{js,ts}
test-*.js
```

### Key Features

- **Test Environment**: jsdom (browser-like)
- **TypeScript**: Full support via ts-jest
- **ES Modules**: Transforms node_modules when needed
- **CSS Mocking**: Uses identity-obj-proxy
- **Timeout**: 30 seconds per test
- **No Fail on Empty**: `--passWithNoTests` flag

### Module Aliases

```javascript
'@/*'           → 'src/*'
'@workflow/core' → 'workflows/core'
```

## Python Testing (Optional)

### pytest Configuration

Create `pytest.ini` for Python test settings:

```ini
[pytest]
testpaths = tests python_tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
```

### Graceful Handling

The test orchestrator treats Python tests as optional:
- **Missing pytest**: Warns and continues
- **No Python tests**: Treats as success
- **Python test failures**: Reports and fails CI

## CI Integration

### GitHub Actions

Your workflows should simply call:

```yaml
- name: Run tests
  run: npm test
```

The orchestrator handles:
- ✅ Running both test suites
- ✅ Proper exit codes
- ✅ Colored output in CI
- ✅ Detailed failure reporting

### Required Environment

```yaml
env:
  NODE_ENV: test
  CI: true
```

### Optional Secrets for Integration Tests

Some tests may require API keys. The test suite will skip tests that require missing secrets:

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
```

**Note**: Missing secrets cause graceful skips, not failures.

## Writing Tests

### JavaScript/TypeScript Tests

```javascript
// src/services/MyService.test.js
import { MyService } from './MyService';

describe('MyService', () => {
  it('should do something', () => {
    const service = new MyService();
    expect(service.doThing()).toBe(true);
  });
});
```

### Python Tests

```python
# tests/test_agent.py
import pytest
from agent import Agent

def test_agent_creation():
    agent = Agent()
    assert agent is not None
```

## Debugging Test Failures

### Local Debugging

```bash
# Run with verbose output
JEST_VERBOSE=true npm run test:js

# Run specific test file
npx jest path/to/test.js

# Run in watch mode
npx jest --watch
```

### CI Debugging

1. **Check the test summary** at the end of CI logs
2. **Look for the ❌ markers** indicating failures
3. **Review the "Failed test files" section** for specific failures
4. **Check for missing dependencies** (ENOENT errors)

## Common Issues and Solutions

### Issue: "Jest not found"

**Solution**: Install dependencies
```bash
npm ci  # or npm install
```

### Issue: "Tests timing out"

**Solution**: Increase timeout in jest.config.js
```javascript
testTimeout: 60000  // 60 seconds
```

### Issue: "Module not found"

**Solution**: Check moduleNameMapper in jest.config.js
```javascript
moduleNameMapper: {
  '^@/(.*)$': '<rootDir>/src/$1'
}
```

### Issue: "ES module errors"

**Solution**: Add to transformIgnorePatterns
```javascript
transformIgnorePatterns: [
  'node_modules/(?!(your-esm-package)/)'
]
```

### Issue: "Python tests fail but should skip"

**Solution**: Ensure pytest exit code 5 (no tests) is handled
The orchestrator automatically treats this as success.

## Test Coverage

### Generate Coverage Report

```bash
# Run Jest with coverage
npx jest --coverage

# View coverage in browser
open coverage/lcov-report/index.html
```

### Coverage Configuration

Edit `jest.config.js`:
```javascript
collectCoverage: true,
collectCoverageFrom: [
  'src/**/*.{js,jsx,ts,tsx}',
  '!src/**/*.test.{js,jsx,ts,tsx}',
  '!**/node_modules/**'
],
coverageThreshold: {
  global: {
    branches: 70,
    functions: 70,
    lines: 70,
    statements: 70
  }
}
```

## Performance Optimization

### Parallel Execution

For large test suites, enable parallel execution:

```bash
# Jest automatically uses workers
npx jest --maxWorkers=4

# Or let Jest decide
npx jest --maxWorkers=50%
```

### Test Caching

Jest caches test results. Clear cache if needed:

```bash
npx jest --clearCache
```

## Best Practices

### 1. **Isolate Tests**
- Each test should be independent
- Use `beforeEach` and `afterEach` for setup/teardown
- Don't rely on test execution order

### 2. **Mock External Dependencies**
```javascript
jest.mock('./api', () => ({
  fetchData: jest.fn().mockResolvedValue({ data: 'mock' })
}));
```

### 3. **Use Descriptive Names**
```javascript
// ❌ Bad
it('works', () => {});

// ✅ Good
it('should return user data when given valid ID', () => {});
```

### 4. **Test Edge Cases**
- Empty inputs
- Null/undefined values
- Error conditions
- Boundary values

### 5. **Keep Tests Fast**
- Avoid real network calls (use mocks)
- Minimize file I/O
- Use test doubles for expensive operations

## Continuous Integration

### Workflow Configuration

Your `.github/workflows/ci.yml` should:

```yaml
name: CI Tests

on:
  push:
    branches: [ main, develop, feat/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
      env:
        NODE_ENV: test
        CI: true
```

### Matrix Testing (Optional)

Test against multiple Node versions:

```yaml
strategy:
  matrix:
    node-version: [18.x, 20.x, 22.x]
```

## Migration Guide

If you're updating from the old test setup:

1. **Update package.json scripts**:
   - `"test": "node run-test-suite-ci.js"`

2. **Update jest.config.js**:
   - Add `--passWithNoTests` flag
   - Update testMatch patterns

3. **Update CI workflows**:
   - Change to `npm test` (not `npm run test:js`)

4. **Test locally**:
   ```bash
   npm test
   ```

## Support

For issues or questions:

1. Check this guide first
2. Review the test orchestrator code: `run-test-suite-ci.js`
3. Check Jest documentation: https://jestjs.io/
4. Check pytest documentation: https://pytest.org/
5. Open an issue on GitHub

---

**Last Updated**: December 2025  
**Maintainer**: Lab Verse Team
