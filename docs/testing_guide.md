# Testing Guide

This guide explains how to test the ai_utilities library, including all test parameters and best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Test Parameters](#test-parameters)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Test Commands

```bash
# Run all tests (unit tests only - no API calls)
pytest

# Run unit tests only (fast, no external dependencies)
pytest -m "not integration"

# Run integration tests (requires API key)
pytest -m "integration"

# Run specific test file
pytest tests/test_files_api.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Environment Setup for Testing

```bash
# Set up test environment
export AI_API_KEY="your-test-key"  # Only for integration tests
export AI_PROVIDER="openai"
export AI_MODEL="test-model"

# Or use .env file for testing
cp .env.example .env.test
# Edit .env.test with test values
```

---

## Test Categories

### 1. Unit Tests (`-m "not integration"`)
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (seconds)
- **Dependencies**: None (uses fake providers)
- **Examples**: `test_files_api.py`, `test_client.py`

### 2. Integration Tests (`-m "integration"`)
- **Purpose**: Test with real APIs
- **Speed**: Slower (minutes)
- **Dependencies**: Requires API keys
- **Examples**: `test_files_integration.py`, `test_real_api_integration.py`

### 3. Performance Tests
- **Purpose**: Test speed and resource usage
- **Speed**: Variable
- **Dependencies**: May require API keys
- **Examples**: `test_performance.py`

---

## Test Parameters

### Pytest Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `-v` | Verbose output | `pytest -v` |
| `-s` | Show stdout (don't capture) | `pytest -s` |
| `-x` | Stop on first failure | `pytest -x` |
| `--tb=short` | Short traceback format | `pytest --tb=short` |
| `--tb=line` | One-line traceback | `pytest --tb=line` |
| `-k "expression"` | Run tests matching expression | `pytest -k "upload"` |
| `--maxfail=N` | Stop after N failures | `pytest --maxfail=3` |

### Marker Parameters

| Marker | Purpose | Usage |
|--------|---------|-------|
| `integration` | Tests requiring real API | `pytest -m integration` |
| `not integration` | Tests without API calls | `pytest -m "not integration"` |
| `openai` | OpenAI-specific tests | `pytest -m openai` |
| `slow` | Slow-running tests | `pytest -m "not slow"` |

### Coverage Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `--cov=src` | Generate coverage report | `pytest --cov=src` |
| `--cov-report=html` | HTML coverage report | `pytest --cov=src --cov-report=html` |
| `--cov-report=term` | Terminal coverage | `pytest --cov=src --cov-report=term` |
| `--cov-fail-under=80` | Fail if coverage < 80% | `pytest --cov=src --cov-fail-under=80` |

---

## Running Tests

### Development Workflow

```bash
# 1. Quick check during development
pytest tests/test_files_api.py -x --tb=line

# 2. Full unit test suite
pytest -m "not integration" -v

# 3. Integration tests (when API available)
pytest -m integration -v

# 4. Full test suite with coverage
pytest --cov=src --cov-report=html

# 5. Performance tests
pytest tests/test_performance.py -v
```

### CI/CD Pipeline

```bash
# In CI/CD (no API keys)
pytest -m "not integration" --cov=src --cov-fail-under=80

# In CI/CD with API keys
pytest --cov=src --cov-fail-under=80
```

### Debugging Tests

```bash
# Run with debugging output
pytest -s -v tests/test_files_api.py::TestFileUpload::test_upload_file_success

# Run with Python debugger
pytest --pdb tests/test_files_api.py::TestFileUpload::test_upload_file_success

# Run with verbose output and stop on failure
pytest -x -v --tb=short tests/test_files_api.py
```

---

## Writing Tests

### Test Structure

```python
import pytest
from ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider

class TestFeatureName:
    """Test feature description."""
    
    def test_method_name(self):
        """Test specific functionality."""
        # Arrange
        settings = AiSettings(api_key='test-key', provider='openai')
        provider = FakeProvider()
        client = AiClient(settings=settings, provider=provider)
        
        # Act
        result = client.some_method()
        
        # Assert
        assert result is not None
        assert result.success == True
```

### Using Fixtures

```python
@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    settings = AiSettings(api_key='test-key', provider='openai')
    provider = FakeProvider()
    return AiClient(settings=settings, provider=provider)

def test_with_fixture(mock_client):
    """Test using fixture."""
    result = mock_client.ask("test prompt")
    assert result is not None
```

### Async Tests

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_functionality():
    """Test async methods."""
    from ai_utilities import AsyncAiClient
    
    settings = AiSettings(api_key='test-key', provider='openai')
    provider = FakeAsyncProvider()
    client = AsyncAiClient(settings=settings, provider=provider)
    
    result = await client.ask("test prompt")
    assert result is not None
```

### Integration Tests

```python
import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("AI_API_KEY"), reason="No API key")
def test_real_api_integration():
    """Test with real API."""
    client = AiClient()  # Uses real API key from environment
    
    result = client.ask("What is AI?")
    assert len(result) > 0
    assert isinstance(result, str)
```

### Error Testing

```python
def test_error_handling():
    """Test error conditions."""
    provider = FakeProvider(should_fail=True)
    client = AiClient(provider=provider)
    
    with pytest.raises(FileTransferError):
        client.upload_file("test.txt")
```

---

## Test Configuration

### pytest.ini Configuration

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
markers =
    integration: Tests requiring real API access
    openai: Tests specific to OpenAI provider
    slow: Tests that take a long time to run
```

### pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config", 
    "--verbose",
    "--tb=short"
]
markers = [
    "integration: Tests requiring real API access",
    "openai: Tests specific to OpenAI provider",
    "slow: Tests that take a long time to run"
]
```

---

## Troubleshooting

### Common Issues

#### 1. Interactive Setup Prompts
**Problem**: Tests ask for API key input
**Solution**: Use explicit settings in tests

```python
# Wrong - triggers interactive setup
client = AiClient(provider=provider)

# Correct - no interactive setup
settings = AiSettings(api_key='test-key', provider='openai')
client = AiClient(settings=settings, provider=provider)
```

#### 2. Input Capture Issues
**Problem**: `OSError: pytest: reading from stdin while output is captured`
**Solution**: Run with `-s` flag or fix test setup

```bash
# Quick fix
pytest -s tests/test_files_api.py

# Proper fix - add explicit settings to test
settings = AiSettings(api_key='test-key')
client = AiClient(settings=settings)
```

#### 3. Integration Test Failures
**Problem**: Integration tests fail without API key
**Solution**: Set environment variables or skip tests

```bash
# Set API key
export AI_API_KEY="your-key"

# Or run unit tests only
pytest -m "not integration"
```

#### 4. Import Errors
**Problem**: Module import failures in tests
**Solution**: Add src to Python path

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Debug Commands

```bash
# Run specific test with debugging
pytest -s -v tests/test_files_api.py::TestFileUpload::test_upload_file_success

# Check which tests would run (dry run)
pytest --collect-only

# Run with maximum verbosity
pytest -vv -s

# Check test markers
pytest --markers
```

### Performance Testing

```bash
# Run tests with timing
pytest --durations=10

# Profile slow tests
pytest --profile

# Memory usage testing
pytest --memprof
```

---

## Best Practices

### 1. Test Organization
- **Unit tests**: Test individual methods/classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

### 2. Test Data
- Use temporary files for file tests
- Clean up resources in teardown
- Use fixtures for common test data

### 3. Assertions
- Be specific with assertions
- Test both success and failure cases
- Use descriptive assertion messages

### 4. Mocking
- Use fake providers for unit tests
- Mock external dependencies
- Keep mocks simple and focused

### 5. Performance
- Keep unit tests fast
- Use markers for slow tests
- Run integration tests separately

---

## Example Test Commands

```bash
# Development workflow
pytest tests/test_files_api.py -x --tb=line
pytest -m "not integration" --cov=src
pytest -m integration -s

# CI/CD pipeline
pytest --cov=src --cov-fail-under=80 --maxfail=3

# Debugging
pytest -s -v tests/test_files_api.py::TestFileUpload::test_upload_file_success
pytest --pdb tests/test_files_api.py

# Performance
pytest --durations=10 tests/test_performance.py
```

---

This testing guide provides comprehensive coverage of all testing aspects in ai_utilities. Use it as a reference for writing, running, and debugging tests.
