# Error Handling Guide

AI Utilities provides a clear hierarchy of exceptions that users can safely catch. Only the exceptions listed below are considered part of the public API.

## 🎯 Public Exception Hierarchy

```
AiUtilitiesError (base class)
├── ConfigurationError
│   └── ProviderConfigurationError
├── ProviderError
│   ├── ProviderCapabilityError
│   └── MissingOptionalDependencyError
├── RateLimitError
└── FileTransferError
```

## 📋 Exception Reference

### AiUtilitiesError
**Base class** for all AI Utilities exceptions.
```python
try:
    # AI Utilities code
except AiUtilitiesError as e:
    print(f"AI Utilities error: {e}")
```

### ConfigurationError
Raised when there's a problem with configuration or settings.
```python
from ai_utilities.providers import ProviderConfigurationError

try:
    client = AiClient(settings=invalid_settings)
except ProviderConfigurationError as e:
    print(f"Configuration error: {e}")
```

### ProviderError
Base class for provider-related errors.

#### ProviderCapabilityError
Raised when a provider doesn't support a requested capability.
```python
from ai_utilities.providers import ProviderCapabilityError

try:
    result = client.ask("prompt", return_format="json")
except ProviderCapabilityError as e:
    print(f"Provider doesn't support this: {e}")
```

#### MissingOptionalDependencyError
Raised when trying to use a provider without installing required extras.
```python
from ai_utilities.providers import MissingOptionalDependencyError

try:
    client = AiClient(provider="openai")  # Without openai extra
except MissingOptionalDependencyError as e:
    print(f"Missing dependency: {e}")
    # Solution: pip install ai-utilities[openai]
```

### RateLimitError
Raised when rate limits are exceeded.
```python
from ai_utilities.rate_limiter import RateLimitError

try:
    # Many rapid requests
    result = client.ask("prompt")
except RateLimitError as e:
    print(f"Rate limited: {e}")
```

### FileTransferError
Raised when file upload/download operations fail.
```python
from ai_utilities.providers import FileTransferError

try:
    result = client.upload_file("document.pdf")
except FileTransferError as e:
    print(f"File operation failed: {e}")
```

## 💡 Best Practices

### 1. Catch Specific Exceptions
```python
# Good - Catch specific exceptions
try:
    result = client.ask("prompt")
except MissingOptionalDependencyError:
    print("Please install: pip install ai-utilities[openai]")
except RateLimitError:
    print("Rate limit exceeded, please wait")
except ProviderError as e:
    print(f"Provider error: {e}")

# Avoid - Too broad
try:
    result = client.ask("prompt")
except Exception:
    print("Something went wrong")  # Not helpful
```

### 2. Handle Missing Dependencies Gracefully
```python
from ai_utilities.providers import MissingOptionalDependencyError

def get_ai_response(prompt: str) -> str:
    try:
        client = AiClient()
        return client.ask(prompt)
    except MissingOptionalDependencyError as e:
        return f"AI features not available: {e}"
    except ProviderError as e:
        return f"AI service error: {e}"
```

### 3. Log Errors for Debugging
```python
import logging
from ai_utilities.providers import ProviderError

logger = logging.getLogger(__name__)

try:
    result = client.ask("prompt")
except ProviderError as e:
    logger.error(f"AI provider error: {e}")
    raise  # Re-raise if you can't handle it
```

## 🔧 Internal Exceptions

The following exceptions are **internal** and may change without notice:
- Cache-related exceptions
- Internal provider exceptions
- Database-related exceptions
- Network-level exceptions

Do not catch these directly - they will be wrapped in the public exceptions above.

## 📝 Migration Guide

If you were catching internal exceptions before:

```python
# Old way (don't do this)
try:
    client.ask("prompt")
except sqlite3.DatabaseError:  # Internal
    pass

# New way (do this)
try:
    client.ask("prompt")
except AiUtilitiesError:  # Public API
    pass
```

## 🚨 What NOT to Catch

Avoid catching these internal exceptions directly:
- `sqlite3.*` exceptions
- `requests.*` exceptions  
- `openai.*` exceptions
- Any exception from `ai_utilities.*` that's not listed above

These are implementation details and may change between versions.
