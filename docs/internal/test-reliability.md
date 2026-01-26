# Test Reliability Guidelines

## Overview

This document outlines the test reliability standards for the ai_utilities project to ensure fast, deterministic, and maintainable tests.

## Test Categories

### Unit Tests
- **Location**: `tests/` directory (excluding `integration/`)
- **Network**: No network access (blocked by conftest.py)
- **Speed**: Fast (< 1 second per test)
- **Isolation**: Fully deterministic, no external dependencies
- **Markers**: None required (default)

### Integration Tests
- **Location**: `tests/integration/` and selected test files
- **Network**: Real API calls to external services
- **Speed**: Slow (may take multiple seconds)
- **Isolation**: Requires API keys and network access
- **Markers**: `@pytest.mark.integration` + provider-specific markers

## Test Markers

### Standard Markers
```python
@pytest.mark.slow          # Tests that take > 1 second
@pytest.mark.integration   # Tests requiring network/API calls
```

### Provider-Specific Markers
```python
@pytest.mark.openai        # Requires OpenAI API key
@pytest.mark.groq          # Requires Groq API key
@pytest.mark.together      # Requires Together AI API key
@pytest.mark.openrouter    # Requires OpenRouter API key
@pytest.mark.ollama        # Requires Ollama server
@pytest.mark.lmstudio      # Requires LM Studio server
```

## Running Tests

### Unit Tests Only (Fast, No Network)
```bash
# Run all unit tests
pytest -m "not integration"

# Run unit tests excluding slow tests
pytest -m "not integration and not slow"

# Run with timeout and strict warnings
pytest -m "not integration" -ra --maxfail=1 -W error::pytest.PytestUnraisableExceptionWarning -W error::RuntimeWarning
```

### Integration Tests (Requires API Keys)
```bash
# Run all integration tests
pytest -m integration

# Run specific provider tests
pytest -m "openai"
pytest -m "integration and openai"
```

### Full Test Suite
```bash
# Run everything (will skip integration tests without API keys)
pytest
```

## Test Requirements

### Unit Tests Must
- ✅ Be deterministic (same result every run)
- ✅ Be fast (< 1 second execution time)
- ✅ Use mocks for external dependencies
- ✅ Use `tmp_path` for file operations
- ✅ Clean up after themselves
- ✅ Work without network access

### Integration Tests Must
- ✅ Be marked with `@pytest.mark.integration`
- ✅ Have proper API key checks
- ✅ Be marked with provider-specific markers
- ✅ Handle network failures gracefully
- ✅ Use realistic test data

### Slow Tests Must
- ✅ Be marked with `@pytest.mark.slow`
- ✅ Have justified delays (TTL expiration, rate limits)
- ✅ Use minimal sleep durations
- ✅ Document why they are slow

## Test Environment

### Network Blocking
- Unit tests have network access automatically blocked
- Integration tests can override network blocking
- Tests can opt-in to network access with fixtures

### File System
- Tests must use `tmp_path` fixture for file operations
- Repository root writes are blocked by guardrails
- Tests run in isolated temporary directories

### Randomness
- Tests must not rely on random behavior
- Use fixed seeds where randomness is required
- Avoid non-deterministic test ordering

## Common Patterns

### Mocking External Dependencies
```python
from unittest.mock import patch, Mock

def test_with_mock():
    with patch('ai_utilities.client.OpenAI') as mock_openai:
        mock_openai.return_value = Mock()
        # Test code here
```

### Testing with Temporary Files
```python
def test_file_operations(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    # Test code here
```

### Integration Test Pattern
```python
import os
import pytest

has_api_key = bool(os.getenv("AI_API_KEY"))
pytestmark = (
    pytest.mark.integration
    if has_api_key
    else pytest.mark.skip(reason="No AI_API_KEY set")
)

def test_integration_feature():
    # Integration test code
    pass
```

## CI/CD Integration

### GitHub Actions
- Unit tests run on every PR/commit
- Integration tests run on main branch and releases
- Slow tests run in separate job
- Tests fail fast on first error

### Local Development
- Run `pytest -m "not integration"` for quick feedback
- Use `pytest -m "integration"` for manual API testing
- Ensure all unit tests pass before committing

## Troubleshooting

### Tests Hanging
- Check for network calls in unit tests
- Verify proper mocking of external dependencies
- Look for infinite loops or blocking operations

### Flaky Tests
- Check for race conditions or timing dependencies
- Ensure proper test isolation
- Verify deterministic test data

### Slow Tests
- Consider if test can be rewritten as unit test
- Use minimal sleep durations
- Mark appropriately with `@pytest.mark.slow`

## Enforcement

### Automated Checks
- CI enforces unit test execution without network
- Policy tests prevent new unmarked integration tests
- Coverage requirements enforced in CI

### Code Review
- Review new tests for proper marking
- Verify integration tests have proper API key handling
- Ensure slow tests are justified

---

For more information, see the [Testing Guide](../user/testing-guide.md) and [Development Setup](../dev/development-setup.md).
