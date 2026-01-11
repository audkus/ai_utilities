# Testing Guide

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_client.py

# Run specific test method
pytest tests/test_client.py::TestAiClient::test_ask_method

# Run with coverage
pytest --cov=ai_utilities --cov-report=html

# Run specific test categories
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only
pytest -m "not slow"       # Skip slow tests
```

### Test Configuration

The project uses `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "openai: marks tests that require OpenAI API",
    "groq: marks tests that require Groq API",
]
```

## Test Architecture

### Test Structure

```
tests/
├── test_client.py              # Main client tests
├── test_async_client.py        # Async client tests
├── test_config_models.py       # Configuration tests
├── test_config_resolver.py     # Configuration resolution tests
├── test_ai_settings_model_field.py  # Pydantic field tests
├── test_cli.py                 # CLI tests
├── knowledge/                  # Knowledge base tests
│   ├── test_indexer.py
│   └── test_search.py
├── provider_monitoring/        # Provider monitoring tests
│   └── test_all_providers_script.py
└── test_data/                  # Test data and fixtures
    ├── audio/
    └── reports/
```

### Test Categories

#### Unit Tests
- Test individual functions and classes
- Fast execution (< 1 second per test)
- No external dependencies
- Mock external services

```python
import pytest
from unittest.mock import Mock
from ai_utilities import AiClient, AiSettings

def test_client_creation():
    """Test that client can be created with settings."""
    settings = AiSettings(provider="openai", api_key="test-key")
    client = AiClient(settings)
    assert client.settings.provider == "openai"
    assert client.settings.api_key == "test-key"

def test_ask_method_mock():
    """Test ask method with mocked provider."""
    mock_provider = Mock()
    mock_provider.ask.return_value = Mock(text="Mock response")
    
    client = AiClient()
    client.provider = mock_provider
    
    result = client.ask("Test question")
    assert result.text == "Mock response"
```

#### Integration Tests
- Test component interactions
- Use real services when appropriate
- Test configuration loading
- Test provider integration

```python
import pytest
import os
from ai_utilities import AiClient

@pytest.mark.integration
def test_real_openai_request():
    """Test real OpenAI API request (requires API key)."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    client = AiClient()
    response = client.ask("What is 2+2?")
    assert "4" in response.text
    assert response.usage.total_tokens > 0
```

#### End-to-End Tests
- Test complete workflows
- Test CLI functionality
- Test setup wizard
- Test file operations

```python
import subprocess
import tempfile
from pathlib import Path

def test_cli_setup_wizard():
    """Test CLI setup wizard end-to-end."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        env_path = f.name
    
    try:
        result = subprocess.run([
            "python", "-m", "ai_utilities", "setup",
            "--mode", "normal", "--dry-run", "--non-interactive"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "AI_PROVIDER=openai" in result.stdout
    finally:
        os.unlink(env_path)
```

## Writing Tests

### Test Structure Guidelines

1. **Use descriptive test names**
2. **Arrange-Act-Assert pattern**
3. **Test one thing per test**
4. **Use appropriate fixtures**
5. **Mock external dependencies**

### Example Test

```python
import pytest
from unittest.mock import patch, Mock
from ai_utilities import AiClient, AiSettings
from ai_utilities.providers.provider_exceptions import ProviderConfigurationError

class TestAiClient:
    """Test suite for AiClient class."""
    
    def test_client_creation_with_explicit_settings(self):
        """Test client creation with explicit settings."""
        # Arrange
        settings = AiSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-3.5-turbo"
        )
        
        # Act
        client = AiClient(settings)
        
        # Assert
        assert client.settings.provider == "openai"
        assert client.settings.api_key == "test-key"
        assert client.settings.model == "gpt-3.5-turbo"
    
    def test_client_missing_api_key_raises_error(self):
        """Test that missing API key raises configuration error."""
        # Arrange
        settings = AiSettings(provider="openai", api_key=None)
        
        # Act & Assert
        with pytest.raises(ProviderConfigurationError):
            AiClient(settings)
    
    @patch('ai_utilities.client.create_provider')
    def test_ask_method_calls_provider(self, mock_create_provider):
        """Test that ask method delegates to provider."""
        # Arrange
        mock_provider = Mock()
        mock_provider.ask.return_value = Mock(text="Response", usage=Mock(total_tokens=10))
        mock_create_provider.return_value = mock_provider
        
        client = AiClient()
        
        # Act
        result = client.ask("Test question")
        
        # Assert
        mock_provider.ask.assert_called_once_with("Test question")
        assert result.text == "Response"
        assert result.usage.total_tokens == 10
```

### Fixtures

```python
import pytest
from ai_utilities import AiSettings

@pytest.fixture
def sample_settings():
    """Provide sample settings for tests."""
    return AiSettings(
        provider="openai",
        api_key="test-key",
        model="gpt-3.5-turbo",
        temperature=0.7
    )

@pytest.fixture
def mock_openai_provider():
    """Provide mock OpenAI provider."""
    provider = Mock()
    provider.ask.return_value = Mock(
        text="Mock response",
        usage=Mock(total_tokens=5)
    )
    return provider

def test_with_fixtures(sample_settings, mock_openai_provider):
    """Test using fixtures."""
    client = AiClient(sample_settings)
    client.provider = mock_openai_provider
    
    result = client.ask("Test")
    assert result.text == "Mock response"
```

## Test Data Management

### Test Files

Test data files are stored in `tests/test_data/`:

```
tests/test_data/
├── audio/              # Audio files for testing
│   ├── test_audio.mp3
│   └── test_audio.wav
└── reports/            # Generated test reports
    └── test_results.json
```

### Environment Variables for Tests

Use `pytest.env` or monkeypatch for test environment:

```python
import pytest
import os

def test_with_environment(monkeypatch):
    """Test with custom environment variables."""
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    
    from ai_utilities import AiSettings
    settings = AiSettings()
    
    assert settings.provider == "openai"
    assert settings.api_key == "test-key"
```

## Performance Testing

### Timing Tests

```python
import time

def test_response_time():
    """Test that responses are within acceptable time."""
    client = AiClient()
    
    start_time = time.time()
    response = client.ask("Simple question")
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 5.0  # Should respond within 5 seconds
```

### Memory Tests

```python
import psutil
import os

def test_memory_usage():
    """Test memory usage doesn't grow excessively."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    client = AiClient()
    
    # Make multiple requests
    for _ in range(100):
        client.ask("Test question")
    
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory
    
    # Memory growth should be reasonable (< 50MB)
    assert memory_growth < 50 * 1024 * 1024
```

## Test Coverage

### Coverage Goals

- **Overall coverage:** > 90%
- **Core modules:** > 95%
- **Provider modules:** > 85%

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=ai_utilities --cov-report=html

# Check coverage threshold
pytest --cov=ai_utilities --cov-fail-under=90

# Generate coverage report in terminal
pytest --cov=ai_utilities --cov-report=term-missing
```

### Coverage Exclusions

```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/test_*",
    "setup.py",
    "*/venv/*",
    "*/.venv/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

## Continuous Integration

### CI Test Configuration

The project uses GitHub Actions for CI:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=ai_utilities
```

## Best Practices

### Do's
- Write descriptive test names
- Test one concept per test
- Use fixtures for common setup
- Mock external dependencies
- Test error conditions
- Use appropriate markers

### Don'ts
- Don't test implementation details
- Don't rely on external services in unit tests
- Don't write tests that are too complex
- Don't ignore test failures
- Don't commit with failing tests

For development setup, see [Development Setup](development-setup.md).
