# Architecture Overview

## High-Level Architecture

AI Utilities follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│              User API                   │
│  AiClient, AsyncAiClient, convenience   │
├─────────────────────────────────────────┤
│            Configuration                │
│  AiSettings, config resolver, env vars  │
├─────────────────────────────────────────┤
│           Provider Layer                │
│  OpenAI, Groq, Ollama, etc.             │
├─────────────────────────────────────────┤
│           Infrastructure                │
│  Caching, rate limiting, error handling │
├─────────────────────────────────────────┤
│              Utilities                  │
│  Audio processing, files, monitoring    │
└─────────────────────────────────────────┘
```

## Core Components

### Client Layer (`client.py`, `async_client.py`)

**Purpose:** Main user-facing API

**Key Classes:**
- `AiClient` - Synchronous client
- `AsyncAiClient` - Asynchronous client
- `create_client()` - Convenience function

**Responsibilities:**
- Provide simple API for AI interactions
- Handle configuration loading
- Coordinate provider selection
- Manage error handling and retries

### Configuration System (`config_models.py`, `config_resolver.py`)

**Purpose:** Manage all configuration and settings

**Key Classes:**
- `AiSettings` - Pydantic-based settings model
- `ConfigurationResolver` - Resolve and validate configuration

**Features:**
- Environment variable loading
- `.env` file support
- Validation and type checking
- Provider-specific defaults

### Provider Layer (`providers/`)

**Purpose:** Abstract different AI providers behind common interface

**Key Classes:**
- `BaseProvider` - Abstract base class
- `OpenAIProvider` - OpenAI implementation
- `GroqProvider` - Groq implementation
- `OllamaProvider` - Local Ollama support

**Interface:**
```python
class BaseProvider:
    def ask(self, prompt: str, **kwargs) -> AskResult
    def ask_batch(self, prompts: List[str], **kwargs) -> List[AskResult]
    def ask_stream(self, prompt: str, **kwargs) -> Iterator[str]
    def list_models(self) -> List[str]
```

### Caching System (`cache/`)

**Purpose:** Reduce API costs and improve response times

**Backends:**
- `MemoryCache` - In-memory caching
- `SQLiteCache` - Persistent file-based caching
- `RedisCache` - Distributed caching

**Features:**
- TTL support
- Namespace isolation
- Cache statistics
- Automatic cleanup

### Setup System (`setup/`)

**Purpose:** Interactive configuration wizard

**Components:**
- `SetupWizard` - Main wizard logic
- CLI interface (`cli.py`)
- Provider-specific setup guidance

## Data Flow

### Typical Request Flow

```
1. User calls client.ask("question")
2. Client loads/validates configuration
3. Provider factory creates appropriate provider
4. Cache layer checks for cached response
5. If cache miss: Provider makes API call
6. Response is cached (if enabled)
7. Response is returned to user
```

### Configuration Loading Flow

```
1. AiSettings() is called
2. Pydantic loads environment variables
3. .env file is loaded (if exists)
4. Defaults are applied
5. Validation occurs
6. Settings are ready for use
```

## Design Patterns

### Factory Pattern

Used for provider creation:

```python
def create_provider(settings: AiSettings, provider: str = None) -> BaseProvider:
    """Create provider instance based on settings."""
    provider_name = provider or settings.provider
    
    if provider_name == "openai":
        return OpenAIProvider(settings)
    elif provider_name == "groq":
        return GroqProvider(settings)
    # ... other providers
```

### Strategy Pattern

Used for different caching backends:

```python
class CacheBackend:
    def get(self, key: str) -> Optional[Any]: pass
    def set(self, key: str, value: Any, ttl: int) -> None: pass
    def delete(self, key: str) -> None: pass

class MemoryCache(CacheBackend): ...
class SQLiteCache(CacheBackend): ...
class RedisCache(CacheBackend): ...
```

### Observer Pattern

Used for usage tracking:

```python
class UsageTracker:
    def track_request(self, usage: UsageData) -> None:
        # Track usage statistics
        pass

class AiClient:
    def __init__(self, usage_tracker: UsageTracker = None):
        self.usage_tracker = usage_tracker or create_usage_tracker()
    
    def ask(self, prompt: str, **kwargs):
        result = self.provider.ask(prompt, **kwargs)
        self.usage_tracker.track_request(result.usage)
        return result
```

## Error Handling Strategy

### Exception Hierarchy

```python
class AIUtilitiesError(Exception):
    """Base exception for all AI Utilities errors."""

class ProviderError(AIUtilitiesError):
    """Base class for provider-related errors."""

class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""

class ProviderAPIError(ProviderError):
    """Raised when provider API returns an error."""

class ProviderRateLimitError(ProviderAPIError):
    """Raised when rate limit is exceeded."""
```

### Error Handling Principles

1. **Fail fast** - Validate configuration early
2. **Clear messages** - Provide actionable error information
3. **Recovery guidance** - Suggest solutions in error messages
4. **Consistent types** - Use specific exception types

## Configuration Architecture

### Settings Model

```python
class AiSettings(BaseSettings):
    """Configuration settings using Pydantic."""
    
    # Core settings
    provider: str = Field(default="openai")
    api_key: Optional[str] = None
    model: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AI_MODEL", "OPENAI_MODEL")
    )
    
    # Behavior settings
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    
    # Infrastructure settings
    cache_enabled: bool = False
    cache_backend: str = "memory"
    cache_ttl_s: int = 3600
    
    class Config:
        env_prefix = "AI_"
        case_sensitive = False
```

### Environment Variable Handling

1. **Priority Order:** Explicit params → Environment → .env → Defaults
2. **Validation:** Pydantic validates all values
3. **Type Coercion:** Automatic type conversion
4. **Error Messages:** Clear validation errors

## Provider Architecture

### Provider Interface

All providers implement the same interface:

```python
from abc import ABC, abstractmethod
from typing import List, Iterator, Optional

class BaseProvider(ABC):
    def __init__(self, settings: AiSettings):
        self.settings = settings
        self._configure_client()
    
    @abstractmethod
    def ask(self, prompt: str, **kwargs) -> AskResult:
        """Make a synchronous request."""
        pass
    
    def ask_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream response (optional implementation)."""
        raise NotImplementedError("Streaming not supported")
    
    def list_models(self) -> List[str]:
        """List available models (optional implementation)."""
        raise NotImplementedError("Model listing not supported")
```

### Provider Implementation Example

```python
class OpenAIProvider(BaseProvider):
    def __init__(self, settings: AiSettings):
        super().__init__(settings)
        self.client = openai.OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url
        )
    
    def ask(self, prompt: str, **kwargs) -> AskResult:
        try:
            response = self.client.chat.completions.create(
                model=self.settings.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )
            
            return AskResult(
                text=response.choices[0].message.content,
                usage=UsageData(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens
                )
            )
        except openai.APIError as e:
            raise ProviderAPIError(f"OpenAI API error: {e}")
```

## Caching Architecture

### Cache Key Strategy

```python
def _generate_cache_key(
    prompt: str, 
    provider: str, 
    model: str, 
    temperature: float,
    **kwargs
) -> str:
    """Generate deterministic cache key."""
    import hashlib
    
    key_data = {
        "prompt": prompt,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "kwargs": sorted(kwargs.items())
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()
```

### Cache Inheritance

```python
class CacheBackend(ABC):
    def get(self, key: str) -> Optional[Any]: pass
    def set(self, key: str, value: Any, ttl: int) -> None: pass
    def clear(self) -> None: pass
    def clear_namespace(self, namespace: str) -> None: pass

class SQLiteCache(CacheBackend):
    def __init__(self, db_path: str, max_entries: int = 1000):
        self.db_path = db_path
        self.max_entries = max_entries
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with proper schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    namespace TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
```

## Module Organization

### Core Modules (`src/ai_utilities/`)

- `__init__.py` - Public API exports
- `client.py` - Main client implementation
- `async_client.py` - Async client
- `config_models.py` - Configuration models
- `config_resolver.py` - Configuration resolution
- `cli.py` - Command-line interface

### Provider Modules (`src/ai_utilities/providers/`)

- `__init__.py` - Provider exports and factory
- `base_provider.py` - Abstract base class
- `openai_provider.py` - OpenAI implementation
- `groq_provider.py` - Groq implementation
- `ollama_provider.py` - Local Ollama support

### Infrastructure Modules (`src/ai_utilities/`)

- `cache/` - Caching backends
- `usage/` - Usage tracking
- `audio/` - Audio processing
- `files/` - File operations

## Extensibility Points

### Adding New Providers

1. Inherit from `BaseProvider`
2. Implement required methods
3. Register in provider factory
4. Add configuration validation
5. Add tests

### Adding New Cache Backends

1. Inherit from `CacheBackend`
2. Implement storage methods
3. Add configuration options
4. Add performance tests

### Adding New Features

1. Follow existing patterns
2. Add proper type hints
3. Include comprehensive tests
4. Update documentation

For testing details, see [Testing Guide](testing.md).
For development setup, see [Development Setup](development-setup.md).
