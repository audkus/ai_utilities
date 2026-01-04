# API Key Setup Guide

This comprehensive guide walks you through setting up API keys for AI Utilities, covering all supported providers and configuration methods.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Supported Providers](#supported-providers)
- [Configuration Methods](#configuration-methods)
- [Provider-Specific Setup](#provider-specific-setup)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## 🚀 Quick Start

### 1. Get Your API Key

Choose your provider and obtain an API key:

- **OpenAI**: [platform.openai.com](https://platform.openai.com/api-keys)
- **Groq**: [console.groq.com](https://console.groq.com/keys)
- **Together AI**: [api.together.xyz](https://api.together.xyz/settings/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)

### 2. Set Environment Variable

```bash
# macOS/Linux
export AI_API_KEY="your-api-key-here"

# Windows PowerShell
$env:AI_API_KEY="your-api-key-here"

# Windows CMD
set AI_API_KEY=your-api-key-here
```

### 3. Start Using AI Utilities

```python
from ai_utilities import create_client

client = create_client()
response = client.ask("Hello, world!")
print(response)
```

---

## 🏢 Supported Providers

### Cloud Providers (Require API Keys)

| Provider | API Key Variable | Base URL | Models |
|----------|------------------|----------|--------|
| **OpenAI** | `AI_API_KEY` or `OPENAI_API_KEY` | `https://api.openai.com/v1` | GPT-4, GPT-3.5, DALL-E |
| **Groq** | `AI_API_KEY` | `https://api.groq.com/openai/v1` | Llama 3, Mixtral, Gemma |
| **Together AI** | `AI_API_KEY` | `https://api.together.xyz/v1` | Llama 3, Mixtral, OpenSource |
| **Anthropic** | `AI_API_KEY` | `https://api.anthropic.com` | Claude 3.5, Claude 3 |
| **OpenRouter** | `AI_API_KEY` | `https://openrouter.ai/api/v1` | Multiple Models |

### Local Providers (Optional API Keys)

| Provider | API Key Required | Base URL | Setup |
|----------|------------------|----------|-------|
| **Ollama** | No | `http://localhost:11434` | `ollama pull llama3` |
| **LM Studio** | No | `http://localhost:1234` | Start LM Studio |
| **Text-Generation-WebUI** | No | `http://localhost:5000` | `python server.py --api` |
| **FastChat** | No | `http://localhost:8000` | `python -m fastchat.serve.api` |

---

## ⚙️ Configuration Methods

### Method 1: Environment Variables (Recommended)

#### Priority Order
1. `AI_API_KEY` (highest priority)
2. `OPENAI_API_KEY` (fallback for OpenAI)
3. Provider-specific variables
4. `.env` file

#### Setup Commands

```bash
# Set primary API key
export AI_API_KEY="sk-your-openai-key"

# Or use OpenAI-specific key
export OPENAI_API_KEY="sk-your-openai-key"

# Optional: Set provider
export AI_PROVIDER="openai"

# Optional: Set custom model
export AI_MODEL="gpt-4"
```

### Method 2: .env File

Create a `.env` file in your project root:

```bash
# AI Utilities Configuration
AI_API_KEY=sk-your-api-key-here
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_BASE_URL=https://api.openai.com/v1

# Optional: Cache settings
AI_CACHE_ENABLED=true
AI_CACHE_TTL_S=3600

# Optional: Request settings
AI_REQUEST_TIMEOUT=120
AI_MAX_RETRIES=3
```

### Method 3: Direct Parameter

```python
from ai_utilities import create_client

# Pass API key directly
client = create_client(api_key="sk-your-key-here")

# Or use settings object
from ai_utilities import AiSettings
settings = AiSettings(api_key="sk-your-key-here")
client = create_client(settings=settings)
```

### Method 4: Interactive Setup

Let AI Utilities guide you through setup:

```python
from ai_utilities import create_client

# Will prompt for API key if missing
client = create_client()
```

---

## 🔧 Provider-Specific Setup

### OpenAI

1. **Get API Key**
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create new secret key
   - Copy the key (starts with `sk-`)

2. **Configure**
   ```bash
   export AI_API_KEY="sk-YourOpenAPIKeyHere"
   export AI_PROVIDER="openai"
   ```

3. **Test**
   ```python
   from ai_utilities import create_client
   client = create_client()
   response = client.ask("Hello from OpenAI!")
   ```

### Groq

1. **Get API Key**
   - Sign up at [Groq Console](https://console.groq.com)
   - Navigate to API Keys
   - Create new key

2. **Configure**
   ```bash
   export AI_API_KEY="gsk_your_groq_key_here"
   export AI_PROVIDER="groq"
   ```

3. **Available Models**
   - `llama3-70b-8192`
   - `mixtral-8x7b-32768`
   - `gemma-7b-it`

### Together AI

1. **Get API Key**
   - Sign up at [Together AI](https://api.together.xyz)
   - Get API key from dashboard

2. **Configure**
   ```bash
   export AI_API_KEY="your-together-ai-key"
   export AI_PROVIDER="together"
   ```

### Anthropic Claude

1. **Get API Key**
   - Visit [Anthropic Console](https://console.anthropic.com)
   - Create API key

2. **Configure**
   ```bash
   export AI_API_KEY="sk-ant-your-key-here"
   export AI_PROVIDER="anthropic"
   ```

### OpenRouter

1. **Get API Key**
   - Sign up at [OpenRouter](https://openrouter.ai)
   - Get API key from settings

2. **Configure**
   ```bash
   export AI_API_KEY="sk-or-your-key-here"
   export AI_PROVIDER="openrouter"
   ```

---

## 🔒 Security Best Practices

### 1. Never Commit API Keys

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

### 2. Use Environment Variables

```bash
# ✅ Good - Environment variable
export AI_API_KEY="sk-your-key"

# ❌ Bad - Hardcoded in code
api_key = "sk-your-key"  # Don't do this!
```

### 3. Rotate Keys Regularly

- Change API keys every 90 days
- Monitor usage for unusual activity
- Revoke unused keys immediately

### 4. Use Minimum Required Permissions

- Only grant necessary scopes
- Use project-specific keys when possible
- Limit key usage to specific IP addresses

### 5. Secure Storage

```bash
# Use key management services
export AI_API_KEY=$(aws secretsmanager get-secret-value --secret-id ai-api-key --query SecretString --output text)

# Or use encrypted files
gpg --decrypt api-key.gpg > .env
```

---

## 🛠️ Troubleshooting

### Common Issues

#### "API key not found" Error

```bash
# Check if environment variable is set
echo $AI_API_KEY

# Or check all AI-related variables
env | grep AI
```

#### "Invalid API key" Error

1. Verify key is correct
2. Check if key has expired
3. Ensure key has required permissions
4. Verify correct provider is selected

#### "Rate limit exceeded" Error

```bash
# Wait and retry, or upgrade your plan
export AI_MAX_RETRIES=3
export AI_REQUEST_TIMEOUT=120
```

#### "Connection failed" Error

```bash
# Check network connectivity
curl -H "Authorization: Bearer $AI_API_KEY" https://api.openai.com/v1/models

# Verify base URL
export AI_BASE_URL="https://api.openai.com/v1"
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from ai_utilities import create_client
client = create_client()
```

### Test Connection

```python
from ai_utilities import create_client

try:
    client = create_client()
    models = client.list_models()
    print(f"Connected! Available models: {len(models)}")
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## 🎛️ Advanced Configuration

### Custom Base URLs

```python
# Use custom endpoints
from ai_utilities import AiSettings, create_client

settings = AiSettings(
    api_key="your-key",
    base_url="https://your-custom-endpoint.com/v1",
    provider="openai_compatible"
)

client = create_client(settings=settings)
```

### Multiple Providers

```python
# Configure different providers
from ai_utilities import create_client

# OpenAI client
openai_client = create_client(provider="openai")

# Groq client  
groq_client = create_client(provider="groq")

# Local Ollama client
ollama_client = create_client(provider="ollama")
```

### Caching Configuration

```python
# Enable response caching
from ai_utilities import AiSettings, create_client

settings = AiSettings(
    api_key="your-key",
    cache_enabled=True,
    cache_ttl_s=3600  # Cache for 1 hour
)

client = create_client(settings=settings)
```

### Retry Configuration

```python
# Configure retry behavior
from ai_utilities import AiSettings, create_client

settings = AiSettings(
    api_key="your-key",
    max_retries=5,
    request_timeout=300  # 5 minutes
)

client = create_client(settings=settings)
```

### Proxy Configuration

```bash
# Set proxy for HTTP requests
export HTTP_PROXY="http://your-proxy:8080"
export HTTPS_PROXY="https://your-proxy:8080"
```

---

## 📝 Environment Variable Reference

### Core Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_API_KEY` | Primary API key | `sk-your-key` |
| `AI_PROVIDER` | AI provider name | `openai`, `groq`, `ollama` |
| `AI_MODEL` | Default model | `gpt-4`, `llama3` |
| `AI_BASE_URL` | Custom API endpoint | `https://api.example.com/v1` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_CACHE_ENABLED` | Enable response caching | `true` |
| `AI_CACHE_TTL_S` | Cache TTL in seconds | `3600` |
| `AI_REQUEST_TIMEOUT` | Request timeout in seconds | `120` |
| `AI_MAX_RETRIES` | Maximum retry attempts | `3` |
| `AI_TEMPERATURE` | Default temperature | `0.7` |
| `AI_MAX_TOKENS` | Default max tokens | `2048` |

### Provider-Specific Variables

| Provider | Variable | Description |
|----------|----------|-------------|
| OpenAI | `OPENAI_API_KEY` | Fallback for OpenAI |
| Anthropic | `ANTHROPIC_API_KEY` | Anthropic-specific key |
| Together | `TOGETHER_API_KEY` | Together AI key |
| Groq | `GROQ_API_KEY` | Groq-specific key |

---

## 🧪 Testing Your Setup

### Basic Test

```python
from ai_utilities import create_client

def test_connection():
    try:
        client = create_client()
        response = client.ask("Hello! This is a test.")
        print(f"✅ Success: {response}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

test_connection()
```

### Comprehensive Test

```python
from ai_utilities import create_client

def comprehensive_test():
    client = create_client()
    
    # Test basic chat
    response = client.ask("What is 2+2?")
    print(f"Chat: {response}")
    
    # Test model listing
    models = client.list_models()
    print(f"Available models: {len(models)}")
    
    # Test structured response
    result = client.ask("List 3 colors", response_format="json")
    print(f"Structured: {result}")

comprehensive_test()
```

---

## 📞 Getting Help

### Resources

- **Documentation**: [AI Utilities Docs](https://github.com/audkus/ai_utilities)
- **Issues**: [GitHub Issues](https://github.com/audkus/ai_utilities/issues)
- **Discussions**: [GitHub Discussions](https://github.com/audkus/ai_utilities/discussions)

### Common Solutions

1. **Key not working**: Double-check key format and permissions
2. **Rate limits**: Implement exponential backoff
3. **Network issues**: Check firewall and proxy settings
4. **Model not found**: Verify model name and availability

### Debug Commands

```bash
# Check environment
env | grep -i ai

# Test API directly
curl -H "Authorization: Bearer $AI_API_KEY" \
     https://api.openai.com/v1/models

# Run diagnostics
python scripts/provider_diagnostic.py
```

---

## 🎉 You're Ready!

With your API key configured, you can now:

- ✅ Use all AI providers through a unified interface
- ✅ Switch between providers seamlessly
- ✅ Leverage advanced features like caching and retries
- ✅ Monitor provider health and performance
- ✅ Scale your AI applications with confidence

Happy coding! 🚀