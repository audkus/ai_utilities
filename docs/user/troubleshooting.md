# Troubleshooting Guide

## Top 5 Common Issues

### 1. "API key is required" Error

**Problem:** Missing or invalid API key configuration.

**Solution:**
```bash
# Run interactive setup
ai-utilities setup

# Or set environment variables
export AI_PROVIDER=openai
export AI_API_KEY=your-api-key-here
export AI_MODEL=gpt-3.5-turbo
```

**Check your .env file:**
```bash
cat .env
# Should contain:
# AI_PROVIDER=openai
# AI_API_KEY=sk-your-key
# AI_MODEL=gpt-3.5-turbo
```

### 2. "Provider not supported" Error

**Problem:** Invalid provider name in configuration.

**Solution:**
```bash
# Valid providers: openai, groq, together, openrouter, ollama, openai_compatible
export AI_PROVIDER=openai  # Use one of these
```

**Common mistakes:**
- `AI_PROVIDER=openai_api` → should be `openai`
- `AI_PROVIDER=OpenAI` → should be lowercase `openai`

### 3. Network Connection Issues

**Problem:** Cannot reach API endpoint.

**Solutions:**
```bash
# Check internet connection
curl -I https://api.openai.com/v1/models

# Check if behind corporate proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# For local providers, check if server is running
curl -I http://localhost:11434/v1/models  # Ollama
```

**Custom base URL for corporate networks:**
```bash
export AI_BASE_URL=https://your-proxy.com/openai/v1
```

### 4. Model Not Found Error

**Problem:** Invalid model name for provider.

**Solution:**
```python
# Check available models programmatically
from ai_utilities import AiClient
client = AiClient()
models = client.list_models()  # If supported
print(models)
```

**Common model names:**
- OpenAI: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- Groq: `llama3-70b-8192`, `llama3-8b-8192`
- Ollama: `llama3`, `codellama`, `mistral`

### 5. Caching Not Working

**Problem:** Responses not being cached.

**Solution:**
```bash
# Enable caching in environment
export AI_CACHE_ENABLED=true
export AI_CACHE_BACKEND=sqlite
export AI_CACHE_TTL_S=3600
```

**Or in code:**
```python
from ai_utilities import AiSettings

settings = AiSettings(
    cache_enabled=True,
    cache_backend="sqlite"
)

client = AiClient(settings)
```

## Configuration Issues

### Environment Variables Not Loading

**Check loading order:**
1. Explicit `AiSettings(...)` parameters
2. Environment variables
3. `.env` file
4. Defaults

**Debug .env loading:**
```python
from ai_utilities import AiSettings
import os

# Check if .env exists
print(f".env exists: {os.path.exists('.env')}")

# Check environment variables
print(f"AI_PROVIDER: {os.getenv('AI_PROVIDER')}")
print(f"AI_API_KEY: {os.getenv('AI_API_KEY')}")

# Try loading settings
try:
    settings = AiSettings()
    print(f"Loaded provider: {settings.provider}")
    print(f"Has API key: {bool(settings.api_key)}")
except Exception as e:
    print(f"Error loading settings: {e}")
```

### Provider-Specific Issues

#### OpenAI
```bash
# Check OpenAI API key
curl -H "Authorization: Bearer $AI_API_KEY" \
     https://api.openai.com/v1/models

# Common error: Invalid API key format
# Should start with "sk-"
```

#### Groq
```bash
# Check Groq API key
curl -H "Authorization: Bearer $AI_API_KEY" \
     https://api.groq.com/openai/v1/models

# Common error: Key doesn't start with "gsk_"
```

#### Ollama (Local)
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Install models if missing
ollama pull llama3
ollama pull codellama
```

## Performance Issues

### Slow Response Times

**Check caching:**
```python
# Enable caching for repeated queries
settings = AiSettings(cache_enabled=True)
client = AiClient(settings)

# First call will be slow (API)
# Second call will be fast (cache)
```

**Check network:**
```bash
# Test API latency
time curl -s https://api.openai.com/v1/completions \
  -H "Authorization: Bearer $AI_API_KEY" \
  -d '{"model":"gpt-3.5-turbo","prompt":"test","max_tokens":1}'
```

### Memory Usage

**For large caches:**
```python
# Use SQLite instead of memory cache
settings = AiSettings(
    cache_backend="sqlite",
    cache_sqlite_max_entries=1000  # Limit cache size
)
```

## Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from ai_utilities import AiClient
client = AiClient()

# This will show detailed request/response info
response = client.ask("Test message")
```

## Getting Help

If you're still stuck:

1. **Check the documentation:** [Configuration Guide](configuration.md)
2. **Run setup wizard:** `ai-utilities setup`
3. **Check GitHub issues:** Search for similar problems
4. **Create minimal reproduction:** Isolate the issue with minimal code

**When reporting issues, include:**
- Provider and model used
- Error message (full traceback)
- Configuration (environment variables, .env file)
- Minimal code example that reproduces the issue

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ProviderConfigurationError` | Missing config | Run `ai-utilities setup` |
| `AuthenticationError` | Invalid API key | Check API key format and value |
| `RateLimitError` | Too many requests | Enable caching, reduce request rate |
| `ConnectionError` | Network issues | Check internet, proxy settings |
| `ModelNotFoundError` | Invalid model | Use correct model name for provider |
