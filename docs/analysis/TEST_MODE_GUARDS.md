# Test-Mode Guards Documentation

## Overview

Test-mode guards are a set of safety mechanisms implemented to prevent test isolation regressions and improve the reliability of the test suite. They automatically detect when tests are running and enforce stricter behavior regarding environment variable access and global state mutations.

## Features

### 1. Automatic Test Mode Detection

The system automatically detects when running in test mode through:
- `pytest` being present in `sys.modules`
- `PYTEST_CURRENT_TEST` environment variable being set
- Explicit `test_mode_guard()` context usage

### 2. Environment Access Warnings

When in test mode, the system warns about:
- **Direct `os.environ` access**: Using `get_safe_env()` generates warnings about direct environment access
- **Nested environment overrides**: Creating nested `override_env()` contexts with conflicting keys generates warnings

### 3. Safe Environment Access

The `get_safe_env()` function provides:
- Contextvar override awareness (checks overrides first)
- Warning generation for direct access in test mode
- Fallback to real environment variables

## Usage

### Basic Usage

```python
from ai_utilities.env_overrides import get_safe_env, override_env

# Safe environment access (warns in test mode)
api_key = get_safe_env("OPENAI_API_KEY")

# Contextvar overrides (respects test mode warnings)
with override_env({"AI_MODEL": "test-model"}):
    settings = AiSettings()  # Uses test-model
```

### Test Mode Guard

```python
from ai_utilities.env_overrides import test_mode_guard

# Explicitly enable test mode guards
with test_mode_guard():
    # Test mode protections are active
    pass
```

## Warning Types

### 1. Direct Environment Access Warning
```
UserWarning: Direct os.environ access detected for 'AI_MODEL' in test mode. 
Consider using override_env() context manager for test isolation.
```

**When triggered**: Using `get_safe_env()` in test mode
**Purpose**: Encourage using proper test isolation patterns

### 2. Nested Override Warning
```
UserWarning: Nested environment overrides detected for keys: ['AI_MODEL']. 
This might indicate test isolation issues. Consider restructuring your test to avoid nested overrides.
```

**When triggered**: Creating nested `override_env()` contexts with conflicting keys
**Purpose**: Prevent confusing test scenarios where overrides might not behave as expected

## Implementation Details

### Test Mode Detection Logic

```python
def is_test_mode() -> bool:
    # Check explicit test mode context first
    if _test_mode.get():
        return True
    
    # Check if pytest is running
    if 'pytest' in sys.modules:
        return True
    
    # Check pytest environment variable
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return True
    
    return False
```

### Automatic Test Mode Activation

Test mode is automatically enabled for all pytest sessions via the `enable_test_mode_guard()` fixture in `tests/conftest.py`:

```python
@pytest.fixture(scope="session", autouse=True)
def enable_test_mode_guard():
    with test_mode_guard():
        yield
```

## Best Practices

### 1. Use `override_env()` for Test Isolation

```python
# ✅ Good - Proper test isolation
def test_something():
    with override_env({"AI_MODEL": "test-model"}):
        # Test logic here
        pass

# ❌ Avoid - Direct environment mutation
def test_something():
    os.environ["AI_MODEL"] = "test-model"  # Will leak between tests
```

### 2. Use `get_safe_env()` for Environment Access

```python
# ✅ Good - Safe with warnings
def get_config():
    model = get_safe_env("AI_MODEL", "gpt-3.5-turbo")
    return model

# ❌ Avoid - No test mode protection
def get_config():
    model = os.environ.get("AI_MODEL", "gpt-3.5-turbo")
    return model
```

### 3. Avoid Nested Overrides with Same Keys

```python
# ✅ Good - Different keys
with override_env({"AI_MODEL": "test-model"}):
    with override_env({"AI_TEMPERATURE": "0.5"}):
        # No warning - different keys
        pass

# ❌ Avoid - Same keys (generates warning)
with override_env({"AI_MODEL": "outer"}):
    with override_env({"AI_MODEL": "inner"}):
        # Warning - nested overrides with same key
        pass
```

## Migration Guide

### For Existing Tests

1. **Replace direct `os.environ` usage**:
   ```python
   # Before
   os.environ["AI_MODEL"] = "test"
   
   # After  
   with override_env({"AI_MODEL": "test"}):
       # test code
   ```

2. **Replace direct environment reads**:
   ```python
   # Before
   model = os.environ.get("AI_MODEL")
   
   # After
   model = get_safe_env("AI_MODEL")
   ```

### For New Code

- Always use `override_env()` for test environment setup
- Use `get_safe_env()` for environment variable access
- Structure tests to avoid nested overrides with conflicting keys

## Benefits

1. **Prevents Test Leakage**: Warnings help identify patterns that cause test isolation issues
2. **Improves Test Reliability**: Encourages proper test isolation patterns
3. **Early Detection**: Issues are caught during development, not in CI
4. **Documentation**: Warnings serve as in-code documentation of best practices
5. **Backward Compatibility**: Existing code continues to work, just with warnings

## Configuration

### Disabling Warnings

If needed, warnings can be filtered:

```python
import warnings
warnings.filterwarnings("ignore", "Direct os.environ access detected")
warnings.filterwarnings("ignore", "Nested environment overrides detected")
```

However, it's recommended to address the underlying issues rather than suppress warnings.

### Debug Mode

Enable debug mode to see more detailed information:

```bash
AI_UTILITIES_TEST_DEBUG=1 pytest
```

This will enable additional logging and debug output during test execution.
