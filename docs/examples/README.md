# Copy/Paste Examples

This section contains documentation-first examples designed for immediate use. No repository cloning required - these work after `pip install ai-utilities`.

## Table of Contents

- [Minimal synchronous call](#minimal-synchronous-call)
- [Minimal .env configuration](#minimal-env-configuration)
- [Minimal async call](#minimal-async-call)
- [Provider selection](#provider-selection)
- [Structured JSON output](#structured-json-output)
- [Caching behavior](#caching-behavior)
- [Local Ollama usage](#local-ollama-usage)

## Minimal synchronous call

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("What is the capital of France?")
print(response)
```

## Minimal .env configuration

Create `.env` with your preferred provider:

```bash
# OpenAI (recommended for beginners)
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Or Groq (fast inference)
# GROQ_API_KEY=your-groq-key  
# GROQ_MODEL=llama3-70b-8192
```

## Minimal async call

```python
import asyncio
from ai_utilities import AsyncAiClient

async def main():
    client = AsyncAiClient()
    response = await client.ask("Explain photosynthesis")
    print(response)

asyncio.run(main())
```

## Provider selection

```python
from ai_utilities import AiClient, AiSettings

# Explicit provider selection
settings = AiSettings(provider="groq", api_key="your-key", model="llama3-70b-8192")
client = AiClient(settings)
response = client.ask("What is machine learning?")
print(response)
```

## Structured JSON output

```python
from ai_utilities import AiClient, parse_json_from_text

client = AiClient()
response = client.ask("List 3 programming languages with their year created")
data = parse_json_from_text(response)
print(data)
```

## Caching behavior

```python
from ai_utilities import AiClient

client = AiClient()

# First call: hits API, costs tokens
result1 = client.ask("What is Python?", cache_namespace="learning")

# Second call: instant response, $0 cost
result2 = client.ask("What is Python?", cache_namespace="learning")

print(result1)
print(result2)
```

## Local Ollama usage

```python
from ai_utilities import AiClient, AiSettings

# Requires local Ollama server running
settings = AiSettings(
    provider="ollama",
    base_url="http://localhost:11434/v1",
    model="llama3.1"
)
client = AiClient(settings)
response = client.ask("Hello, local model!")
print(response)
```

## Running the Examples

### Prerequisites

```bash
pip install ai-utilities[openai]
```

### Setup Environment Variables

Choose one provider and set the required variables:

```bash
# Option 1: OpenAI
export OPENAI_API_KEY=your-openai-key
export OPENAI_MODEL=gpt-4o-mini

# Option 2: Groq
export GROQ_API_KEY=your-groq-key
export GROQ_MODEL=llama3-70b-8192

# Option 3: Use .env file instead
echo "OPENAI_API_KEY=your-key" > .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
```

### Run Any Example

```bash
# Save any example above to demo.py
python demo.py
```

### Run Local Ollama Example

```bash
# Start Ollama server first
ollama serve

# Pull the model
ollama pull llama3.1

# Set environment and run
export OLLAMA_BASE_URL=http://localhost:11434/v1
export OLLAMA_MODEL=llama3.1
python demo.py  # Where demo.py contains the Ollama example
```

## Notes

- Examples use the stable v1.x public API
- No error handling included for brevity
- All examples are production-ready with proper imports
- Environment variables are loaded automatically from `.env` if present
- Local providers require the respective server to be running
