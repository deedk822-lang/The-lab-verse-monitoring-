# Testing Quick Reference

## 🚀 Quick Start

```bash
# Run all tests (recommended)
npm test

# Run only JavaScript/TypeScript tests
npm run test:js

# Run only Python tests
npm run test:py

# Run integration tests
npm run test:integration
```

## 📚 Documentation

For comprehensive testing information:

- **[CI Testing Guide](./CI_TESTING_GUIDE.md)** - Complete guide to running tests, debugging, and best practices
- **[Professional CI Fixes Summary](./CI_FIXES_COMPLETE_PROFESSIONAL.md)** - Technical overview of the testing infrastructure

## ✅ What's Tested

### JavaScript/TypeScript (Jest)
- Unit tests: `*.test.{js,ts,tsx}`
- Integration tests: `tests/**/*.test.js`
- Component tests: `**/*.spec.{js,tsx}`

### Python (pytest) - Optional
- Unit tests: `test_*.py`
- Integration tests: `tests/**/*_test.py`

## 🐛 Common Issues

### "Error: no test specified"

**Solution**: You're on an old version. Pull latest changes:
```bash
git pull origin feat/vaal-ai-empire-fixes
npm ci
npm test
```

### Tests timeout

**Solution**: Tests have 30s timeout. If you need more:
```bash
npx jest --testTimeout=60000
```

### Module not found

**Solution**: Clear cache and reinstall:
```bash
npm run lint:fix  # Fix any import issues
npx jest --clearCache
npm ci
npm test
```

## 🛠️ CI Integration

### GitHub Actions

Tests run automatically on:
- Push to `main`, `develop`, `feat/*` branches
- Pull requests to `main`, `develop`

### Required Setup

No secrets required for basic tests. Optional secrets for integration tests:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`

Missing secrets cause graceful skips, not failures.

## 📊 Test Results

After running tests, you'll see:

```
======================================================================
📊 TEST SUITE SUMMARY
======================================================================
✅ JEST: PASSED
   12 tests passed in 2 suites
   
✅ PYTEST: PASSED (skipped)
   Reason: pytest-missing
   
======================================================================

🎉 All test suites completed successfully!
⏱️  Total time: 8.42s

💚 CI tests passed! Ready to merge.
```

## 📖 Writing Tests

### JavaScript Example

```javascript
// src/services/auth.test.js
import { authenticate } from './auth';

describe('authenticate', () => {
  it('should return token for valid credentials', async () => {
    const token = await authenticate('user', 'pass');
    expect(token).toBeDefined();
    expect(typeof token).toBe('string');
  });
  
  it('should throw error for invalid credentials', async () => {
    await expect(
      authenticate('user', 'wrong')
    ).rejects.toThrow('Invalid credentials');
  });
});
```

### Python Example

```python
# tests/test_agent.py
import pytest
from agent import Agent

def test_agent_initialization():
    agent = Agent(name="TestAgent")
    assert agent.name == "TestAgent"
    assert agent.is_active is False

def test_agent_activation():
    agent = Agent(name="TestAgent")
    agent.activate()
    assert agent.is_active is True
```

## 🚀 Advanced Usage

### Watch Mode (Development)

```bash
npx jest --watch
```

### Coverage Report

```bash
npx jest --coverage
open coverage/lcov-report/index.html
```

### Debug Specific Test

```bash
# Run single test file
npx jest src/auth.test.js

# Run tests matching pattern
npx jest --testNamePattern="should authenticate"

# Verbose output
npx jest --verbose
```

## 🔗 Related Documentation

- [CI Testing Guide](./CI_TESTING_GUIDE.md) - Complete testing documentation
- [Professional CI Fixes](./CI_FIXES_COMPLETE_PROFESSIONAL.md) - Technical implementation details
- [Jest Configuration](./jest.config.js) - Test configuration
- [Test Orchestrator](./run-test-suite-ci.js) - Test runner source code

## 👤 Getting Help

1. Check [CI_TESTING_GUIDE.md](./CI_TESTING_GUIDE.md) for detailed troubleshooting
2. Review test orchestrator logs for specific errors
3. Open an issue with:
   - Full error output
   - Steps to reproduce
   - Environment info (Node version, OS)

---

**Last Updated**: December 2025  
**Maintained by**: Lab Verse Team
