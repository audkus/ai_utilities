# AI Utilities

A Python library for AI model interaction with unified interface, intelligent caching, and type safety. Use OpenAI, Groq, Together AI, Ollama, and other providers with the same code.

## Who This Is For

AI Utilities is for developers who need to integrate AI capabilities into their applications without being locked into a single provider. It's designed for both beginners who want simple AI interactions and advanced users who need production-ready features like caching and rate limiting.

## What Problem It Solves

Managing multiple AI providers is complex and error-prone. Each provider has different APIs, authentication methods, and error handling. AI Utilities solves this by providing a single, consistent interface that works across all major providers while adding enterprise features like intelligent caching and comprehensive error handling.

## Quickstart

### Install

```bash
pip install ai-utilities[openai]
```

### Basic Usage

```python
from ai_utilities import AiClient

# Create client (loads from .env file automatically)
client = AiClient()

# Make a request
response = client.ask("What is the capital of France?")
print(response)

# Monitor usage (if tracking enabled)
usage_stats = client.get_usage_stats()
if usage_stats:
    print(f"Tokens used: {usage_stats.total_tokens}")
```

### Configuration

Create a `.env` file:

```bash
AI_PROVIDER=openai
AI_API_KEY=your-api-key-here
AI_MODEL=gpt-3.5-turbo
```

Or run the interactive setup:

```bash
ai-utilities setup
```

## Common Usage Examples

### With Caching

```python
from ai_utilities import AiClient

client = AiClient()

# What is caching?
# Caching stores AI responses locally so identical questions 
# get instant answers without API calls or costs.

# Ask questions with intelligent caching
result = client.ask(
    "Explain quantum computing in simple terms",
    cache_namespace="learning"  # Groups related cached responses
)

print(result.text)

# First call: Hits API, costs tokens, stores response
# Second call (same question): Instant response, $0 cost
```

### Different Providers

```python
from ai_utilities import AiClient, AiSettings

# Use Groq instead of OpenAI
settings = AiSettings(
    provider="groq",
    api_key="your-groq-key",
    model="llama3-70b-8192"
)

client = AiClient(settings)
response = client.ask("What is machine learning?")
```

### Async Usage

```python
import asyncio
from ai_utilities import AsyncAiClient

async def main():
    client = AsyncAiClient()
    response = await client.ask("Hello, world!")
    print(response)

asyncio.run(main())
```

## Supported Providers

- **OpenAI** - GPT-4, GPT-3.5-turbo, audio processing
- **Groq** - Fast inference with Llama models
- **Together AI** - Open source models
- **OpenRouter** - Multiple model access
- **Ollama** - Local server support
- **OpenAI Compatible** - Custom endpoints

## Troubleshooting

### Top 5 Common Issues

1. **"API key is required"**
   ```bash
   ai-utilities setup
   # Or set: export AI_API_KEY=your-key
   ```

2. **"Provider not supported"**
   ```bash
   export AI_PROVIDER=openai  # Use lowercase name
   ```

3. **Network connection issues**
   ```bash
   # Check internet connection
   curl -I https://api.openai.com/v1/models
   ```

4. **Model not found**
   ```bash
   # Use correct model names:
   # OpenAI: gpt-4, gpt-3.5-turbo
   # Groq: llama3-70b-8192
   ```

5. **Caching not working**
   ```bash
   export AI_CACHE_ENABLED=true
export AI_CACHE_BACKEND=sqlite
```

## Testing

### Running Tests

This project uses pytest with timeout protection to prevent hanging tests.

#### Unit Tests (Fast)
```bash
# Run unit tests only (no external API calls)
pytest -m "not integration" --timeout=30
```

#### Integration Tests (Requires API Keys)
```bash
# Set up API key first
export AI_API_KEY=your-api-key

# Run integration tests
pytest -m "integration" --timeout=120
```

#### All Tests
```bash
# Run all tests with appropriate timeouts
pytest -m "not integration" --timeout=30  # Unit tests
pytest -m "integration" --timeout=120     # Integration tests (if API key available)
```

### Test Timeouts

- **Unit tests**: 30 seconds per test (fail fast)
- **Integration tests**: 120 seconds per test (allow for network latency)
- **Request timeouts**: 30 seconds default (configurable via `AI_TIMEOUT`)

### Test Categories

- **Unit tests**: Fast tests without external dependencies
- **Integration tests**: Tests that call real APIs (marked with `@pytest.mark.integration`)

Integration tests are automatically skipped if API keys are missing.

For detailed testing guidelines, see [CI_TIMEOUT_GUIDELINES.md](CI_TIMEOUT_GUIDELINES.md).

## Where to Go Next

### User Documentation
- [Getting Started Guide](docs/user/getting-started.md) - Detailed setup and examples
- [Configuration Guide](docs/user/configuration.md) - All environment variables
- [Provider Setup](docs/user/providers.md) - Provider-specific configuration
- [Smart Caching](docs/user/caching.md) - Reduce API costs with caching
- [Troubleshooting Guide](docs/user/troubleshooting.md) - Common issues and solutions

### Development
- For development setup see [CONTRIBUTING.md](CONTRIBUTING.md)
- [Development Documentation](docs/dev/development-setup.md)
- [Architecture Overview](docs/dev/architecture.md)
- [Testing Guide](docs/dev/testing.md)

For development setup and contributing, see CONTRIBUTING.md

---

MIT License - see [LICENSE](LICENSE) file for details.
