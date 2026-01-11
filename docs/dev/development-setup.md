# Development Setup

## Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities
```

### 2. Create Virtual Environment

```bash
# Using venv
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n ai_utilities python=3.9
conda activate ai_utilities
```

### 3. Install Development Dependencies

```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Or install specific extras
pip install -e ".[dev,test]"  # Development and testing
pip install -e ".[dev,audio]"  # With audio support
pip install -e ".[dev,all]"    # Everything
```

### 4. Verify Installation

```bash
# Run tests to verify setup
pytest

# Check CLI functionality
python -m ai_utilities --help
ai-utilities setup --dry-run --non-interactive
```

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with proper type hints and docstrings

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Check code quality:**
   ```bash
   ruff check .
   ruff format .
   mypy src/
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### Code Quality Tools

The project uses several code quality tools:

#### Ruff (Linting & Formatting)

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

#### MyPy (Type Checking)

```bash
# Type check the codebase
mypy src/

# Check specific module
mypy src/ai_utilities/client.py
```

#### Pre-commit Hooks (Optional)

```bash
# Install pre-commit hooks
pre-commit install

# Hooks will run automatically on commit
```

## Project Structure

```
ai_utilities/
├── src/ai_utilities/           # Main package
│   ├── __init__.py            # Public API exports
│   ├── client.py              # Main client implementation
│   ├── async_client.py        # Async client
│   ├── config_models.py       # Configuration models
│   ├── config_resolver.py     # Configuration resolution
│   ├── cli.py                 # Command-line interface
│   ├── setup/                 # Setup wizard
│   │   ├── __init__.py
│   │   └── wizard.py
│   ├── providers/             # Provider implementations
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   └── ...
│   ├── cache/                 # Caching backends
│   │   ├── __init__.py
│   │   ├── memory_cache.py
│   │   └── sqlite_cache.py
│   └── ...
├── tests/                     # Test suite
│   ├── test_client.py
│   ├── test_config_models.py
│   └── ...
├── docs/                      # Documentation
│   ├── user/                  # User documentation
│   └── dev/                   # Developer documentation
├── pyproject.toml            # Project configuration
├── README.md                 # User-facing README
└── CONTRIBUTING.md           # Development guide
```

## Key Development Concepts

### Configuration System

The library uses Pydantic for configuration:

```python
from ai_utilities.config_models import AiSettings
from pydantic import Field

class AiSettings(BaseSettings):
    provider: str = Field(default="openai")
    api_key: Optional[str] = None
    model: Optional[str] = None
    
    class Config:
        env_prefix = "AI_"
```

### Provider Architecture

All providers inherit from `BaseProvider`:

```python
from ai_utilities.providers.base_provider import BaseProvider

class CustomProvider(BaseProvider):
    def ask(self, prompt: str, **kwargs) -> AskResult:
        # Implementation here
        pass
```

### Error Handling

Use specific exception types:

```python
from ai_utilities.providers.provider_exceptions import (
    ProviderConfigurationError,
    ProviderAPIError,
    ProviderRateLimitError
)

if not settings.api_key:
    raise ProviderConfigurationError("API key is required")
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_client.py

# Run with coverage
pytest --cov=ai_utilities

# Run specific test markers
pytest -m "not slow"  # Skip slow tests
pytest -m "unit"      # Run only unit tests
```

### Test Structure

```python
import pytest
from ai_utilities import AiClient

class TestAiClient:
    def test_client_creation(self):
        client = AiClient()
        assert client is not None
    
    def test_ask_method(self):
        client = AiClient()
        response = client.ask("Test")
        assert response.text is not None
```

### Test Categories

- **Unit tests**: Fast, test individual components
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test full workflows
- **Performance tests**: Test speed and memory usage

## Adding New Features

### Adding a New Provider

1. **Create provider class:**
   ```python
   # src/ai_utilities/providers/new_provider.py
   from ai_utilities.providers.base_provider import BaseProvider
   
   class NewProvider(BaseProvider):
       def ask(self, prompt: str, **kwargs) -> AskResult:
           # Implementation
           pass
   ```

2. **Register provider:**
   ```python
   # src/ai_utilities/providers/provider_factory.py
   from .new_provider import NewProvider
   
   PROVIDERS["new_provider"] = NewProvider
   ```

3. **Add tests:**
   ```python
   # tests/test_new_provider.py
   def test_new_provider():
       provider = NewProvider(settings)
       result = provider.ask("test")
       assert result is not None
   ```

4. **Update documentation:**
   - Add to provider list in docs/user/providers.md
   - Update configuration examples

### Adding Configuration Options

1. **Add to settings model:**
   ```python
   # src/ai_utilities/config_models.py
   class AiSettings(BaseSettings):
       new_option: str = Field(default="default_value")
   ```

2. **Add environment variable:**
   ```python
   # Add AI_NEW_OPTION to documentation
   ```

3. **Add tests:**
   ```python
   def test_new_option():
       settings = AiSettings(new_option="test")
       assert settings.new_option == "test"
   ```

## Debugging

### Enabling Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed HTTP requests, responses, etc.
client = AiClient()
```

### Common Development Issues

- **Import errors:** Ensure PYTHONPATH includes `src/`
- **Type errors:** Run `mypy src/` to check
- **Test failures:** Check environment configuration
- **Documentation:** Keep docs in sync with code

For more detailed information, see:
- [Testing Guide](testing.md)
- [Architecture Overview](architecture.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
