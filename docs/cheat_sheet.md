# AI Utilities Cheat Sheet

If you remember one thing: AiClient.ask() always returns a plain Python string.

Quick reference for installation, commands, and troubleshooting.

## Installation Commands

```bash
# Basic installation
pip install ai-utilities

# With OpenAI support (recommended)
pip install "ai-utilities[openai]"

# Development installation
pip install "ai-utilities[dev]"
```

## Environment Variables

### Core Variables
```bash
# Primary provider selection
AI_PROVIDER=auto
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Alternative providers
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama3-70b-8192
TOGETHER_API_KEY=your-together-key
OPENROUTER_API_KEY=your-openrouter-key
```

### Local Providers
```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1

# FastChat
FASTCHAT_BASE_URL=http://localhost:8000/v1
FASTCHAT_MODEL=your-model

# Text Generation WebUI
TEXT_GENERATION_WEBUI_BASE_URL=http://localhost:5000/v1
TEXT_GENERATION_WEBUI_MODEL=your-model
```

### Optional Settings
```bash
AI_CACHE_ENABLED=true
AI_CACHE_BACKEND=sqlite
AI_REQUEST_TIMEOUT_S=30
AI_LOG_LEVEL=INFO
```

## Quick Commands

### Sanity Checks
```python
# Basic connectivity
python -c "from ai_utilities import AiClient; print(AiClient().ask('2+2='))"

# Check provider
python -c "from ai_utilities import AiClient; client = AiClient(); print(f'Provider: {client.settings.provider}')"

# Test embeddings
python -c "from ai_utilities import AiClient; print(len(AiClient().get_embeddings(['test'])[0]))"
```

### Testing Commands
```bash
# Unit tests
pytest -m "not integration" --timeout=30

# Integration tests (requires API keys)
AI_UTILITIES_LOAD_DOTENV=1 pytest -m integration --timeout=120

# Coverage testing
tox -e coverage
```

## Common Troubleshooting

### Missing API Key
```
Error: API key is required
```
**Solution:** Set environment variable or create `.env` file:
```bash
export OPENAI_API_KEY=your-key
# or
echo "OPENAI_API_KEY=your-key" > .env
```

### Missing Optional Dependency
```
Error: No module named 'openai'
```
**Solution:** Install with extras:
```bash
pip install "ai-utilities[openai]"
```

### Base URL Issues
```
Error: Connection refused
```
**Solution:** Check provider URL and server status:
```bash
# For Ollama
curl http://localhost:11434/api/tags

# For custom endpoints
curl -H "Authorization: Bearer $key" https://your-endpoint.com/v1/models
```

### Import Errors
```
Error: cannot import name 'AiClient'
```
**Solution:** Ensure correct installation and Python version:
```bash
pip install --upgrade ai-utilities
python --version  # Should be 3.8+
```

## Quick Setup

```python
from ai_utilities import AiClient, AsyncAiClient

# Sync client
client = AiClient()

# Async client
async_client = AsyncAiClient()
```

## Core Methods

### Text Generation
```python
response = client.ask("What is AI?")
data = client.ask("List 3 models", return_format="json")
responses = client.ask_many(["Q1", "Q2", "Q3"])
```

### Embeddings
```python
texts = ["Hello", "World"]
embeddings = client.get_embeddings(texts)
print(f"Vector length: {len(embeddings[0])}")
```

### Files
```python
# Upload
uploaded = client.upload_file("document.pdf")

# List
files = client.list_files()

# Download
content = client.download_file("file-id")
```

### Audio
```python
# Transcribe
result = client.transcribe_audio("audio.wav")
print(result['text'])

# Validate
validate_audio_file("audio.wav")
```

### Images
```python
# Generate
image_bytes = client.generate_image("A red circle")

# Save
with open("image.png", "wb") as f:
    f.write(image_bytes)
```

### Knowledge
```python
# Index documents
client.index_knowledge("reports/")

# Search with knowledge
response = client.ask_with_knowledge("What are the findings?")
```

### Usage Tracking
```python
# Make requests
client.ask("What is machine learning?")

# Check usage
client.print_usage_summary()
stats = client.get_usage_stats()
```

## Configuration

### Environment Setup
```python
from ai_utilities import AiClient, AiSettings

# Custom provider
settings = AiSettings(
    provider="groq",
    api_key="your-key",
    model="llama3-70b-8192"
)
client = AiClient(settings)
```

### Custom Endpoint
```python
settings = AiSettings(
    provider="openai-compatible",
    base_url="https://api.example.com/v1",
    api_key="your-key",
    model="your-model"
)
```

## Error Handling

```python
from ai_utilities.providers.provider_exceptions import (
    ProviderCapabilityError,
    FileTransferError
)

try:
    result = client.generate_image("A dog")
except ProviderCapabilityError as e:
    print(f"Provider doesn't support: {e.capability}")
except FileTransferError as e:
    print(f"File operation failed: {e}")
```

## Links to Detailed Documentation

- [Examples and tutorials](examples/README.md)
- [File operations](files.md)
- [Audio processing](audio_processing.md)
- [Caching guide](caching.md)
- [Provider troubleshooting](provider_troubleshooting.md)
- [Main README](../README.md)

**Save this cheat sheet for quick reference when building with ai_utilities!**
