# Configuration Guide

## Basic Configuration

### Environment Variables

The library supports both generic and provider-specific environment variables:

#### Auto-Selection (Recommended)
```bash
# Let ai_utilities automatically select among configured providers
AI_PROVIDER=auto

# Optional: Override auto-selection order
AI_AUTO_SELECT_ORDER=openai,groq,openrouter,together,ollama,fastchat,text-generation-webui
```

#### Generic Variables (Legacy Support)
```bash
# Required for explicit provider selection
AI_PROVIDER=openai
AI_API_KEY=your-api-key-here
AI_MODEL=gpt-3.5-turbo

# Optional
AI_BASE_URL=https://custom-endpoint.com/v1
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1000
```

#### Provider-Specific Variables (New Format)
```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

# Groq
GROQ_API_KEY=gsk_your-groq-key
GROQ_MODEL=llama3-70b-8192

# Together AI
TOGETHER_API_KEY=your-together-key
TOGETHER_MODEL=mistral-7b

# OpenRouter
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=anthropic/claude-3-haiku

# Local Providers (require base URL and model)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1

FASTCHAT_BASE_URL=http://localhost:8000/v1
FASTCHAT_MODEL=your-model-name

TEXT_GENERATION_WEBUI_BASE_URL=http://localhost:5000/v1
TEXT_GENERATION_WEBUI_MODEL=your-model-name

# OpenAI Compatible (custom endpoints)
AI_BASE_URL=https://your-endpoint.com/v1
AI_API_KEY=your-key
AI_MODEL=your-model
```

### .env File Support

Create a `.env` file in your project root:

```bash
# Auto-selection (recommended)
AI_PROVIDER=auto

# Configure multiple providers
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

GROQ_API_KEY=gsk_your-groq-key
GROQ_MODEL=llama3-70b-8192

OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1
```

The library automatically loads `.env` files when present.

### Interactive Setup

Run the setup wizard for guided configuration:

```bash
ai-utilities setup
```

This provides:
- Provider selection with explanations
- API key configuration
- Model selection guidance
- Automatic .env file creation

## Configuration Precedence

Settings load in this order (highest to lowest priority):

1. Explicit `AiSettings(...)` parameters
2. Environment variables (`os.environ`)
3. `.env` file values (loaded via `pydantic-settings`)
4. Provider-specific variables (fallback to generic)
5. Defaults

### Auto-Selection Behavior

When `AI_PROVIDER=auto` (default), the library:

1. **Detects configured providers** by checking provider-specific variables
2. **Selects deterministically** based on `AI_AUTO_SELECT_ORDER` (default: `openai,groq,openrouter,together,ollama,fastchat,text-generation-webui`)
3. **Logs the selection** at INFO level for transparency
4. **Falls back gracefully** if preferred provider isn't configured

**Example auto-selection:**
```bash
# Multiple providers configured
OPENAI_API_KEY=sk-key1
GROQ_API_KEY=gsk-key2
OLLAMA_BASE_URL=http://localhost:11434/v1

# AI_PROVIDER=auto will select OpenAI (first in order)
# If OpenAI key is missing, will select Groq
# If both missing, will select Ollama (if model specified)
```

## Complete Environment Variables

### Core Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_PROVIDER` | Yes | - | Provider: `openai`, `groq`, `together`, `openrouter`, `ollama`, `openai_compatible` |
| `AI_API_KEY` | Yes for most providers | - | API key for the provider |
| `AI_MODEL` | Yes | - | Model name to use |
| `AI_BASE_URL` | No | Provider-specific | Custom API base URL |

### Behavior Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_TEMPERATURE` | No | 0.7 | Response randomness (0.0-2.0) |
| `AI_MAX_TOKENS` | No | - | Maximum response tokens |
| `AI_TIMEOUT` | No | 30 | Request timeout in seconds |

### Caching Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_CACHE_ENABLED` | No | false | Enable response caching |
| `AI_CACHE_BACKEND` | No | memory | Cache backend: `memory`, `sqlite`, `redis` |
| `AI_CACHE_TTL_S` | No | 3600 | Cache time-to-live in seconds |

### Usage Tracking

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_USAGE_SCOPE` | No | per_client | Usage tracking scope |
| `AI_USAGE_CLIENT_ID` | No | - | Custom client ID for tracking |

## Provider-Specific Configuration

### OpenAI

```bash
# Provider-specific (recommended)
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

# Generic (legacy)
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
AI_MODEL=gpt-4
```

### Groq

```bash
# Provider-specific (recommended)
GROQ_API_KEY=gsk_your-groq-key
GROQ_MODEL=llama3-70b-8192

# Generic (legacy)
AI_PROVIDER=groq
AI_API_KEY=gsk_your-groq-key
AI_MODEL=llama3-70b-8192
```

### Ollama (Local)

```bash
# Provider-specific (recommended)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1

# Generic (legacy)
AI_PROVIDER=ollama
AI_MODEL=llama3.1
AI_BASE_URL=http://localhost:11434/v1
# Note: API key not required for local providers
```

### OpenAI-Compatible (Custom)

```bash
# Generic (required for custom endpoints)
AI_PROVIDER=openai_compatible
AI_API_KEY=your-custom-key
AI_MODEL=your-custom-model
AI_BASE_URL=https://your-endpoint.com/v1
```

### Auto-Selection Example

```bash
# Configure multiple providers
AI_PROVIDER=auto
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

GROQ_API_KEY=gsk_your-groq-key
GROQ_MODEL=llama3-70b-8192

OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1

# Library will auto-select OpenAI (first in order)
# If OpenAI fails, will try Groq, then Ollama
```

## Programmatic Configuration

```python
from ai_utilities import AiClient, AiSettings

# Explicit configuration
settings = AiSettings(
    provider="openai",
    api_key="your-key",
    model="gpt-4",
    temperature=0.5,
    max_tokens=2000
)

client = AiClient(settings)
```

## Configuration Validation

The library validates configuration and provides clear error messages:

```python
from ai_utilities import AiClient
from ai_utilities.providers.provider_exceptions import ProviderConfigurationError

try:
    client = AiClient()  # Will load from .env or environment
except ProviderConfigurationError as e:
    print(f"Configuration error: {e}")
    print("Run: ai-utilities setup")
```

Common errors:
- Missing API key for cloud providers
- Invalid provider name
- Unsupported model for provider
- Network connectivity issues

For troubleshooting, see [Troubleshooting Guide](troubleshooting.md).
