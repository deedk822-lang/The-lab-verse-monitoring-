# Rainmaker Orchestrator Test Suite

## Overview

This directory contains comprehensive unit tests for the Rainmaker Orchestrator project, covering all major components added or modified in the current feature branch.

## Test Files

### Core Tests

1. **`test_healer.py`** - Self-Healing Agent Tests
   - Tests alert handling and hotfix generation
   - Covers error scenarios and edge cases
   - Tests integration with Kimi client
   - ~380+ lines, 22+ test methods

2. **`test_kimi_client.py`** - Kimi API Client Tests
   - Tests API client initialization and configuration
   - Covers content generation in different modes
   - Tests error handling and health checks
   - ~450+ lines, 31+ test methods

3. **`test_core_orchestrator.py`** - Core Orchestrator Tests
   - Tests task execution (Python, Shell, Docker modes)
   - Covers workspace management
   - Tests timeout and error handling
   - ~150+ lines, 10+ test methods

4. **`test_config.py`** - Configuration Tests
   - Tests settings initialization from environment
   - Covers default value handling
   - Tests all configuration parameters
   - ~260+ lines, 29+ test methods

### Background Worker Tests

5. **`../tests/test_background_worker.py`** - Background Worker Tests
   - Tests rate limiting functionality
   - Covers SSRF protection mechanisms
   - Tests HTTP job processing
   - ~470+ lines, 32+ test methods

### Shared Fixtures

6. **`conftest.py`** - Pytest Configuration
   - Provides shared test fixtures
   - Includes `temp_workspace`, `mock_env_vars`, etc.
   - Simplifies test setup across modules

## Running Tests

### Run All Tests
```bash
cd /home/jailuser/git
pytest rainmaker_orchestrator/tests/ tests/test_background_worker.py -v
```

### Run Specific Test File
```bash
pytest rainmaker_orchestrator/tests/test_healer.py -v
pytest rainmaker_orchestrator/tests/test_kimi_client.py -v
pytest rainmaker_orchestrator/tests/test_core_orchestrator.py::TestOrchestratorInitialization -v
```

### Run with Coverage
```bash
pytest --cov=rainmaker_orchestrator --cov=agents.background \
       --cov-report=html --cov-report=term-missing
```

### Run Specific Test Method
```bash
pytest rainmaker_orchestrator/tests/test_healer.py::TestSelfHealingAgentHandleAlert::test_handle_alert_success -v
```

## Test Organization

Tests are organized into logical classes based on functionality:

- **Initialization Tests**: Test object creation and setup
- **Functionality Tests**: Test core features and happy paths
- **Error Handling Tests**: Test exception handling and failure modes
- **Edge Case Tests**: Test boundary conditions and unusual inputs
- **Integration Tests**: Test interactions between components

## Dependencies

Tests require the following packages (from `requirements.txt`):
- `pytest >= 8.3.4`
- `pytest-cov` (for coverage reports)
- `python-dotenv`
- `openai` (for Kimi client tests)
- `httpx`, `fastapi`, `uvicorn`

## Testing Best Practices Applied

✅ **Isolation**: Each test is independent and doesn't rely on others  
✅ **Mocking**: External dependencies are mocked to ensure fast, reliable tests  
✅ **Descriptive Names**: Test names clearly describe what they test  
✅ **Comprehensive Coverage**: Happy paths, error cases, and edge cases all covered  
✅ **Setup/Teardown**: Proper cleanup of resources after tests  
✅ **Documentation**: All test classes and complex tests have docstrings  

## Coverage Summary

| Module | Test File | Coverage | Test Count |
|--------|-----------|----------|------------|
| `agents/healer.py` | `test_healer.py` | ~95% | 22+ tests |
| `clients/kimi.py` | `test_kimi_client.py` | ~95% | 31+ tests |
| `core/orchestrator.py` | `test_core_orchestrator.py` | ~80% | 10+ tests |
| `config.py` | `test_config.py` | ~100% | 29+ tests |
| `background/worker.py` | `test_background_worker.py` | ~85% | 32+ tests |

**Total: 124+ test methods across 5 test files**

## CI/CD Integration

These tests are designed for CI/CD pipelines:
- Fast execution (< 60 seconds total)
- No external service dependencies
- Deterministic results
- Clear failure messages
- Compatible with GitHub Actions and other CI systems

## Future Enhancements

Potential areas for expansion:
- Performance benchmarks and load testing
- Integration tests with real services (separate CI stage)
- Property-based testing with `hypothesis`
- Mutation testing to verify test quality
- API contract testing

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add docstrings to test classes and complex tests
3. Use appropriate fixtures from `conftest.py`
4. Ensure tests are isolated and can run independently
5. Mock external dependencies
6. Update this README with new test files

## Questions?

Refer to:
- `TEST_COVERAGE_SUMMARY.md` for detailed coverage information
- Individual test files for specific testing patterns
- `conftest.py` for available fixtures