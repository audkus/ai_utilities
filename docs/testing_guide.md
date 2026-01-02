# Testing Guide

This guide explains how to test the ai_utilities library, including all test parameters, categories, and best practices.

## 📊 Test Categories

The test suite is organized into three main categories:

### 🧪 Unit Tests (535 tests)
- **Speed**: Fast (no external dependencies)
- **Requirements**: No API keys needed
- **Purpose**: Core functionality testing
- **Examples**: `test_caching.py`, `test_client.py`, `test_config_models.py`

### 🔗 Integration Tests (54 skipped by default)
- **Speed**: Medium (requires API calls)
- **Requirements**: Valid API keys needed
- **Purpose**: Real API interaction testing
- **Examples**: Live provider tests, file upload tests
- **Run with**: `pytest -m integration` (requires `AI_API_KEY`)

### 📈 Dashboard Tests (17 deselected by default)
- **Speed**: Slow (runs full test suite)
- **Requirements**: None, but makes real API calls
- **Purpose**: Test suite validation and reporting
- **Examples**: `test_dashboard.py`
- **Run with**: `pytest -m dashboard`

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Understanding Test Output](#understanding-test-output)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Basic Test Commands

```bash
# Run all tests (unit tests only - no API calls)
pytest
# Output: 535 passed, 54 skipped, 17 deselected in 105.24s

# Run unit tests only (fast, no external dependencies)
pytest -m "not integration and not dashboard"

# Run integration tests (requires API key)
pytest -m integration
# First set: export AI_API_KEY="your-key"

# Run dashboard validation tests
pytest -m dashboard
# Note: These are slow and make real API calls

# Run specific test file
pytest tests/test_files_api.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## 📖 Understanding Test Output

### What the Numbers Mean

```
535 passed, 54 skipped, 17 deselected in 105.24s (0:01:45)
```

- **535 passed**: Unit tests that ran successfully
- **54 skipped**: Integration tests that require API keys or external services
- **17 deselected**: Dashboard tests excluded by configuration filter

### Why Tests Are Skipped/Deselected

**Skipped Tests (54):**
- Integration tests without `AI_API_KEY`
- Tests requiring external services (Ollama, local providers)
- Platform-specific tests

**Deselected Tests (17):**
- Dashboard validation tests (`@pytest.mark.dashboard`)
- Excluded by `pytest.ini` setting: `addopts = -m "not dashboard"`
- These run the actual test suite and are slow

### Test Markers

```bash
# See all available markers
pytest --markers

# Common markers:
# @pytest.mark.integration - Requires API keys
# @pytest.mark.hanging - Tests that hang in full suite
# @pytest.mark.dashboard - Dashboard validation tests
```

---

## 🏃 Running Tests

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

### Test Selection Strategies

```bash
# Fast feedback: unit tests only
pytest

# Full feedback: include integration tests
pytest -m "not dashboard"

# Complete validation: include dashboard tests
pytest -m "dashboard"

# Specific functionality
pytest tests/test_caching.py -v
pytest tests/test_client.py::test_ai_client_creation -v

# Exclude slow tests
pytest -m "not hanging and not dashboard"
```

### CI/CD Testing

```bash
# CI environment (no API keys)
pytest -m "not integration and not dashboard"

# Full CI with API keys
pytest -m "not dashboard"
```

---

## ✍️ Writing Tests

### Test Structure

```python
import pytest
from ai_utilities import AiClient, AiSettings
from tests.test_caching import FakeProvider

def test_functionality():
    """Test description."""
    # Arrange
    fake_settings = AiSettings(temperature=0.5)
    provider = FakeProvider(fake_settings)
    client = AiClient(settings=settings, provider=provider)
    
    # Act
    response = client.ask("test prompt")
    
    # Assert
    assert "test prompt" in response
    assert provider.ask_count == 1
```

### Testing with Cache

```python
def test_caching_behavior(tmp_path):
    """Test cache isolation and behavior."""
    import tempfile
    
    # SQLite cache requires explicit path in pytest
    settings = AiSettings(
        cache_enabled=True,
        cache_backend="sqlite",
        cache_sqlite_path=tmp_path / "test_cache.sqlite",
        cache_namespace="test"
    )
    
    client = AiClient(settings=settings)
    
    # Test cache hit
    response1 = client.ask("test")
    response2 = client.ask("test")  # Should hit cache
    
    assert response1 == response2
```

### Integration Tests

```python
@pytest.mark.integration
def test_real_api_call():
    """Test with real API - requires AI_API_KEY."""
    client = AiClient()
    response = client.ask("What is 2+2?")
    assert "4" in response or "four" in response.lower()
```

### Dashboard Tests

```python
@pytest.mark.dashboard
def test_dashboard_validation():
    """Test dashboard functionality - slow validation test."""
    # These tests run the full test suite
    # Only run when explicitly requested
    pass
```

---

## 🔧 Troubleshooting

### Common Issues

**Tests are too slow:**
```bash
# Exclude dashboard tests (default behavior)
pytest

# Check what's running
pytest --collect-only | wc -l  # Should show ~589 total
```

**Integration tests failing:**
```bash
# Check API key
echo $AI_API_KEY

# Run without integration tests
pytest -m "not integration"
```

**Cache tests failing:**
```bash
# SQLite cache needs explicit path in pytest
export AI_CACHE_SQLITE_PATH="/tmp/test_cache.sqlite"
pytest tests/test_sqlite_cache.py -v
```

**Database/connection errors:**
```bash
# Clean test environment
rm -rf .pytest_cache/
pytest --tb=short
```

### Debugging Test Selection

```bash
# See which tests will run
pytest --collect-only -m "not dashboard"

# See deselected tests
pytest --collect-only -m dashboard

# Check test markers
grep -r "@pytest.mark" tests/ | head -10
```

### Performance Issues

```bash
# Run with timing information
pytest --durations=10

# Profile slow tests
pytest --profile

# Run in parallel (if available)
pytest -n auto
```

---

## 📚 Best Practices

1. **Use FakeProvider for unit tests** - Avoid real API calls
2. **Mark integration tests** - Use `@pytest.mark.integration`
3. **Test cache behavior** - Include cache hit/miss scenarios
4. **Use tmp_path for files** - Clean test isolation
5. **Test error conditions** - Don't just test happy paths
6. **Keep tests fast** - Avoid unnecessary delays
7. **Use descriptive names** - Test should document itself

---

## 📖 Related Documentation

- [Smart Caching Guide](caching.md) - Testing with cache backends
- [Command Reference](command_reference.md) - All configuration options
- [Test Dashboard](test_dashboard.md) - Dashboard validation tests
