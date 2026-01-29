# Contributing to AI Utilities

Thank you for your interest in contributing to AI Utilities! This guide covers development setup, contribution guidelines, and technical details.

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- Virtual environment tool

### Setup Commands

```bash
# Clone repository
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Verify setup
pytest
python -m ai_utilities --help
```

## Development Workflow

### Making Changes

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** with proper type hints and docstrings

3. **Run quality checks:**
   ```bash
   ruff check .          # Linting
   ruff format .         # Formatting
   mypy src/            # Type checking
   pytest              # Tests
   ```

4. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Quality Tools

### Required Tools

```bash
# Install development tools (included in [dev] extra)
pip install ruff mypy pytest pytest-cov
```

### Commands

```bash
# Lint and auto-fix
ruff check . --fix

# Format code
ruff format .

# Type checking
mypy src/

# Run tests with coverage
pytest --cov=ai_utilities
```

### Pre-commit Setup (Optional)

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# hooks run automatically on commit
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_client.py

# With coverage
pytest --cov=ai_utilities --cov-report=html

# Specific test categories
pytest -m "unit"          # Unit tests only
pytest -m "integration"   # Integration tests
pytest -m "not slow"      # Skip slow tests
```

### Test Structure

- **Unit tests:** Fast, no external dependencies
- **Integration tests:** Component interactions
- **End-to-end tests:** Complete workflows
- **Provider tests:** Real API calls (requires keys)

### Writing Tests

```python
import pytest
from unittest.mock import Mock
from ai_utilities import AiClient, AiSettings

def test_client_creation():
    """Test client creation with settings."""
    settings = AiSettings(provider="openai", api_key="test-key")
    client = AiClient(settings)
    assert client.settings.provider == "openai"

@pytest.mark.integration
def test_real_api_call():
    """Test real API call (requires OPENAI_API_KEY)."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    client = AiClient()
    response = client.ask("What is 2+2?")
    assert "4" in response.text
```

## Adding Features

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

2. **Register in factory:**
   ```python
   # src/ai_utilities/providers/provider_factory.py
   PROVIDERS["new_provider"] = NewProvider
   ```

3. **Add configuration:**
   ```python
   # src/ai_utilities/config_models.py
   class AiSettings(BaseSettings):
       # Add provider-specific settings
   ```

4. **Add tests:**
   ```python
   # tests/test_new_provider.py
   def test_new_provider():
       # Test implementation
       pass
   ```

5. **Update documentation:**
   - Add to `docs/user/providers.md`
   - Update configuration examples

### Adding Configuration Options

1. **Add to AiSettings:**
   ```python
   # src/ai_utilities/config_models.py
   class AiSettings(BaseSettings):
       new_option: str = Field(default="default_value")
   ```

2. **Add validation:**
   ```python
   @field_validator('new_option')
   def validate_new_option(cls, v):
       # Validation logic
       return v
   ```

3. **Add tests:**
   ```python
   def test_new_option():
       settings = AiSettings(new_option="test")
       assert settings.new_option == "test"
   ```

## Project Structure

```
ai_utilities/
├── src/ai_utilities/           # Main package
│   ├── __init__.py            # Public API
│   ├── client.py              # Main client
│   ├── async_client.py        # Async client
│   ├── config_models.py       # Configuration
│   ├── config_resolver.py     # Config resolution
│   ├── cli.py                 # CLI interface
│   ├── providers/             # Provider implementations
│   │   ├── base_provider.py   # Abstract base
│   │   ├── openai_provider.py # OpenAI
│   │   └── ...
│   ├── cache/                 # Caching backends
│   ├── usage/                 # Usage tracking
│   └── setup/                 # Setup wizard
├── tests/                     # Test suite
├── docs/                      # Documentation
│   ├── user/                  # User docs
│   └── dev/                   # Developer docs
├── pyproject.toml            # Project config
├── README.md                 # User README
└── CONTRIBUTING.md           # This file
```

## Code Standards

### Style Guidelines

- **Type hints** required for all public functions
- **Docstrings** using Google style for public functions/classes
- **Maximum line length** 88 characters (ruff default)
- **Import order:** Standard library → Third-party → Local

### Example Code Style

```python
"""Module docstring."""

from typing import Optional
from pydantic import Field

from ai_utilities.config_models import BaseSettings


class ExampleSettings(BaseSettings):
    """Example configuration class.
    
    Attributes:
        example_field: Description of the field.
        optional_field: Description of optional field.
    """
    
    example_field: str = Field(
        default="default_value",
        description="Field description"
    )
    optional_field: Optional[str] = None
    
    def example_method(self, param: str) -> str:
        """Example method.
        
        Args:
            param: Description of parameter.
            
        Returns:
            Processed result.
        """
        return param.upper()
```

### Error Handling

```python
from ai_utilities.providers.provider_exceptions import (
    ProviderConfigurationError,
    ProviderAPIError
)

def validate_settings(settings: AiSettings) -> None:
    """Validate configuration settings.
    
    Args:
        settings: Settings to validate.
        
    Raises:
        ProviderConfigurationError: If configuration is invalid.
    """
    if not settings.api_key and settings.provider in ["openai", "groq"]:
        raise ProviderConfigurationError(
            f"API key required for provider '{settings.provider}'"
        )
```

## Pull Request Process

### Before Submitting

1. **Run all tests:** `pytest`
2. **Check code quality:** `ruff check . && mypy src/`
3. **Update documentation:** Add new features to relevant docs
4. **Test manually:** Verify your changes work as expected

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Error handling considered
```

## Getting Help

### Resources

- **Documentation:** [docs/index.md](docs/index.md)
- **Architecture:** [docs/dev/architecture.md](docs/dev/architecture.md)
- **Testing:** [docs/dev/testing.md](docs/dev/testing.md)
- **User Guide:** [docs/user/getting-started.md](docs/user/getting-started.md)

### Asking Questions

1. **Check existing documentation** first
2. **Search GitHub issues** for similar problems
3. **Create new issue** with:
   - Clear description of problem
   - Minimal reproduction example
   - Environment details (Python version, OS, etc.)

### Reporting Bugs

When reporting bugs, include:
- **Error message** and full traceback
- **Minimal code example** that reproduces the issue
- **Environment information** (Python version, OS, package versions)
- **Expected vs actual behavior**

## Development Tips

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use breakpoints in development
import pdb; pdb.set_trace()
```

### Common Issues

- **Import errors:** Ensure PYTHONPATH includes `src/`
- **Type errors:** Run `mypy src/` to check
- **Test failures:** Check environment configuration
- **Documentation:** Keep docs in sync with code

Thank you for contributing to AI Utilities! Your contributions help make this project better for everyone.
