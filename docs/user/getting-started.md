# Getting Started

## Why This Library Exists

AI Utilities provides a unified interface for multiple AI providers with built-in caching, rate limiting, and type safety. Instead of learning different SDKs, you use one consistent API.

## Compared to Using Provider SDK Directly

| Feature | Direct SDK | AI Utilities |
|---------|------------|--------------|
| Multi-provider | Separate SDKs needed | Single interface |
| Caching | Manual implementation | Built-in, automatic |
| Rate Limits | Manual tracking | Automatic management |
| Type Safety | Basic types | Full Pydantic models |
| Error Handling | Provider-specific | Unified exceptions |

## Who Is It For

- Production teams building AI-powered applications
- Startups needing cost control through intelligent caching
- Enterprise developers requiring type safety and monitoring
- Data scientists experimenting with multiple providers

## When to Use AI Utilities

✅ **Multi-provider projects** - Switch between OpenAI, Groq, Together, etc. without code changes  
✅ **Production applications** - Need caching, rate limiting, and error handling  
✅ **Team collaboration** - Standardized patterns and consistent interfaces  
✅ **Cost-sensitive applications** - Built-in usage tracking and caching  
✅ **Testing environments** - Mock providers and deterministic testing  
✅ **Rapid prototyping** - Quick setup with sensible defaults  

## When NOT to Use AI Utilities

❌ **Simple one-off scripts** - Overhead not justified for single API calls  
❌ **Ultra-low latency requirements** - Direct SDK has minimal overhead  
❌ **Provider-specific optimizations** - Need deep integration with one provider  
❌ **Memory-constrained environments** - Additional layer adds memory footprint  
❌ **Learning provider APIs** - Want to learn raw OpenAI/Groq/etc. APIs directly

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
print(response.text)

# Monitor usage
print(f"Tokens used: {response.usage.total_tokens}")
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

## Key Benefits

- **Single Interface** - Use OpenAI, Groq, Together AI, Ollama with the same code
- **Smart Caching** - Automatic response caching reduces costs and improves speed
- **Rate Limiting** - Built-in protection against API throttling
- **Type Safety** - Full Pydantic integration with mypy support
- **Error Handling** - Unified exceptions with clear error messages

## Common Usage Patterns

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
    print(response.text)

asyncio.run(main())
```

For more detailed information, see:
- [Configuration Guide](configuration.md)
- [Provider Setup](providers.md)
- [Smart Caching](caching.md)
