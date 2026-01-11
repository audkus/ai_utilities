# Configuration Guide

## Basic Configuration

### Environment Variables

The core library reads configuration from environment variables:

```bash
# Required
AI_PROVIDER=openai
AI_API_KEY=your-api-key-here
AI_MODEL=gpt-3.5-turbo

# Optional
AI_BASE_URL=https://custom-endpoint.com/v1
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1000
```

### .env File Support

Create a `.env` file in your project root:

```bash
# AI Utilities Configuration
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
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
4. Defaults

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
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
AI_MODEL=gpt-3.5-turbo
# AI_BASE_URL=https://api.openai.com/v1  # Default, can be omitted
```

### Groq

```bash
AI_PROVIDER=groq
AI_API_KEY=gsk_your-groq-key
AI_MODEL=llama3-70b-8192
# AI_BASE_URL=https://api.groq.com/openai/v1  # Default
```

### Ollama (Local)

```bash
AI_PROVIDER=ollama
# AI_API_KEY not required for local providers
AI_MODEL=llama3
AI_BASE_URL=http://localhost:11434/v1
```

### OpenAI-Compatible (Custom)

```bash
AI_PROVIDER=openai_compatible
AI_API_KEY=your-custom-key
AI_MODEL=your-custom-model
AI_BASE_URL=https://your-endpoint.com/v1
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
