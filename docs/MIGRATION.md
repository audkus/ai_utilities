# Migration Guide: AI Utilities v1.0

This guide helps you migrate from earlier versions of AI Utilities to the stable v1.0 release.

## 🎯 What's New in v1.0

### Stable Public API
The v1.0 release defines a stable public API that will remain consistent throughout the v1.x series.

**Stable Imports:**
```python
from ai_utilities import (
    AiClient,           # Main synchronous AI client
    AsyncAiClient,      # Asynchronous AI client  
    AiSettings,         # Configuration settings
    create_client,      # Client factory function
    AskResult,          # Response result type
    UploadedFile,       # File upload model
    JsonParseError,     # JSON parsing error
    parse_json_from_text,  # JSON parsing utility
    # Audio processing (stable but may move to submodule later)
    AudioProcessor,
    load_audio_file,
    save_audio_file,
    # Usage tracking
    UsageTracker,
    create_usage_tracker
)
```

### Breaking Changes from Pre-1.0

#### 1. Import Location Changes
**Before (pre-1.0):**
```python
# Some imports may have been from different locations
from ai_utilities.client import AiSettings
from ai_utilities.config_models import SomeConfig
```

**After (v1.0):**
```python
# All stable imports are from the main package
from ai_utilities import AiSettings, AiClient
```

#### 2. Configuration Model Relocation
The `AiSettings` class has been moved from `client.py` to `config_models.py` for better code organization, but this doesn't affect users as it's imported from the main package.

#### 3. Removed Internal APIs
Some internal APIs that were previously accessible have been marked as private or removed:

**Removed:**
```python
# These internal APIs are no longer available
from ai_utilities.client import _internal_function
from ai_utilities.providers._internal import InternalClass
```

**Use stable alternatives:**
```python
# Use the public API instead
from ai_utilities import AiClient, create_client
```

## 🔄 Migration Steps

### Step 1: Update Imports
Update your imports to use the stable public API:

**Find and replace these patterns:**
```python
# Old imports
from ai_utilities.client import AiClient, AiSettings
from ai_utilities.async_client import AsyncAiClient
from ai_utilities.config_models import SomeConfig

# New imports
from ai_utilities import AiClient, AiSettings, AsyncAiClient
```

### Step 2: Update Configuration
If you were using internal configuration models, switch to `AiSettings`:

**Before:**
```python
from ai_utilities.config_models import InternalConfig
config = InternalConfig(some_setting="value")
```

**After:**
```python
from ai_utilities import AiSettings
settings = AiSettings(some_setting="value")
```

### Step 3: Update Provider Usage
If you were directly importing providers, use the factory function:

**Before:**
```python
from ai_utilities.providers.openai_provider import OpenAIProvider
provider = OpenAIProvider(settings)
```

**After:**
```python
from ai_utilities import create_client, AiSettings
settings = AiSettings(provider="openai", api_key="your-key")
client = create_client(settings)
```

### Step 4: Update Error Handling
Some internal exception types have been consolidated:

**Before:**
```python
from ai_utilities.providers._exceptions import InternalError
```

**After:**
```python
from ai_utilities.providers import ProviderCapabilityError, FileTransferError
```

## 📋 Migration Checklist

### ✅ Required Changes
- [ ] Update all imports to use `from ai_utilities import ...`
- [ ] Replace direct provider imports with `create_client()`
- [ ] Update any usage of removed internal APIs
- [ ] Test with your existing configuration

### ✅ Recommended Changes
- [ ] Add error handling for new exception types
- [ ] Update logging to use the new structured format
- [ ] Review caching configuration for new options
- [ ] Add monitoring using the new usage tracking features

### ✅ Optional Changes
- [ ] Migrate to the new configuration management system
- [ ] Implement the new rate limiting features
- [ ] Add circuit breaker patterns for reliability
- [ ] Set up the new monitoring and alerting

## 🧪 Testing Your Migration

### 1. Basic Functionality Test
```python
from ai_utilities import AiClient, AiSettings

def test_basic_functionality():
    """Test that basic functionality works after migration."""
    settings = AiSettings(api_key="test-key", model="test-model")
    client = AiClient(settings)
    
    # This should work without errors
    response = client.ask("Hello, world!")
    print(f"✅ Basic test passed: {response}")

test_basic_functionality()
```

### 2. Configuration Test
```python
from ai_utilities import AiSettings

def test_configuration():
    """Test that your configuration still works."""
    try:
        # Load your existing configuration
        settings = AiSettings()  # Will load from environment
        
        print(f"✅ Configuration loaded:")
        print(f"  Model: {settings.model}")
        print(f"  Temperature: {settings.temperature}")
        print(f"  Cache enabled: {settings.cache_enabled}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")

test_configuration()
```

### 3. Import Test
```python
def test_imports():
    """Test that all your imports work."""
    try:
        from ai_utilities import (
            AiClient, AsyncAiClient, AiSettings, create_client,
            AskResult, UploadedFile, JsonParseError, parse_json_from_text
        )
        print("✅ All stable imports work")
    except ImportError as e:
        print(f"❌ Import error: {e}")

test_imports()
```

## 🔧 Common Migration Issues

### Issue 1: Missing Internal API
**Error:** `ImportError: cannot import name '_internal_function'`

**Solution:** Replace with the public API equivalent:
```python
# Instead of internal function
from ai_utilities import create_client
client = create_client(settings)
```

### Issue 2: Configuration Model Changes
**Error:** `AttributeError: 'AiSettings' object has no attribute 'old_setting'`

**Solution:** Update your configuration to use the new settings:
```python
# Old way
settings = AiSettings(old_setting="value")

# New way
settings = AiSettings(new_setting="value")
```

### Issue 3: Provider Import Changes
**Error:** `ImportError: cannot import name 'OpenAIProvider'`

**Solution:** Use the factory function:
```python
# Old way
from ai_utilities.providers.openai_provider import OpenAIProvider
provider = OpenAIProvider(settings)

# New way
from ai_utilities import create_client
client = create_client(settings)
```

## 📦 Dependency Updates

### Python Version
- **Minimum:** Python 3.8 (same as before)
- **Recommended:** Python 3.9+ for better performance

### Core Dependencies
- `pydantic`: Updated to v2.x (breaking changes if you were using v1.x)
- `pydantic-settings`: Now required for configuration
- `openai`: Updated to latest version

### Optional Dependencies
No changes to optional dependencies.

## 🚀 Performance Improvements in v1.0

### 1. Better Caching
- New SQLite backend with persistence
- Improved cache key generation
- Better namespace isolation

### 2. Enhanced Type Safety
- Full mypy compatibility
- Better type annotations throughout
- Stricter validation

### 3. Improved Error Handling
- More specific exception types
- Better error messages
- Graceful degradation

## 🆘 Getting Help

If you encounter issues during migration:

1. **Check the documentation:** [docs/README.md](docs/README.md)
2. **Review the reliability guide:** [docs/reliability_guide.md](docs/reliability_guide.md)
3. **Check existing issues:** [GitHub Issues](https://github.com/your-repo/ai_utilities/issues)
4. **Create a new issue:** Include your code, error message, and environment details

### Example Issue Report
```markdown
## Migration Issue: Import Error

### Code
```python
from ai_utilities import AiClient, AiSettings
```

### Error
```
ImportError: cannot import name 'AiClient' from 'ai_utilities'
```

### Environment
- Python 3.9.6
- ai-utilities version: 1.0.0
- OS: macOS

### Steps to Reproduce
1. Install ai-utilities 1.0.0
2. Run the import statement
3. Error occurs
```

## ✅ Migration Complete!

Once you've completed these steps and verified everything works, you're successfully migrated to AI Utilities v1.0!

**What you get:**
- ✅ Stable public API that won't break in v1.x releases
- ✅ Better performance and reliability
- ✅ Enhanced type safety and validation
- ✅ Comprehensive documentation and examples
- ✅ Production-ready features

**Next steps:**
- Review the [reliability guide](docs/reliability_guide.md) for production deployment
- Check out the [examples/](examples/) directory for usage patterns
- Set up monitoring and alerting as described in the reliability guide

Welcome to AI Utilities v1.0! 🎉
