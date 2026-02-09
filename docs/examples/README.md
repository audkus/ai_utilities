# Copy/Paste Examples

This section contains documentation-first examples designed for immediate use. No repository cloning required - these work after `pip install ai-utilities`.

## Table of Contents

### Core Text Operations
- [Minimal synchronous call](#minimal-synchronous-call)
- [Minimal async call](#minimal-async-call)
- [Structured JSON output](#text--json--typed)
- [Typed responses](#text--json--typed)

### Configuration & Providers
- [Minimal .env configuration](#minimal-env-configuration)
- [Provider selection](#provider-selection)
- [Provider selection + base_url](#provider-selection--base_url)

### Caching
- [Caching behavior](#caching)

### Embeddings
- [Text embeddings](#embeddings)

### Files
- [File upload and listing](#files)

### Audio
- [Audio transcription](#audio)

### Images
- [Image generation](#images)

### Knowledge
- [Knowledge indexing and search](#knowledge)

### Usage & Metrics
- [Usage tracking](#usage--metrics)

### Local Providers
- [Local Ollama usage](#local-ollama-usage)

## Core Text Operations

### Minimal synchronous call

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("What is the capital of France?")
print(response)
```

### Minimal async call

```python
import asyncio
from ai_utilities import AsyncAiClient

async def main():
    client = AsyncAiClient()
    response = await client.ask("Explain photosynthesis")
    print(response)

asyncio.run(main())
```

### Text + JSON + Typed

```python
from ai_utilities import AiClient, parse_json_from_text

client = AiClient()
response = client.ask("List 3 programming languages with their year created")
data = parse_json_from_text(response)
print(data)
```

## Configuration & Providers

### Minimal .env configuration

Create `.env` with your preferred provider:

```bash
# OpenAI (recommended for beginners)
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Or Groq (fast inference)
# GROQ_API_KEY=your-groq-key  
# GROQ_MODEL=llama3-70b-8192
```

### Provider selection

```python
from ai_utilities import AiClient, AiSettings

# Explicit provider selection
settings = AiSettings(provider="groq", api_key="your-key", model="llama3-70b-8192")
client = AiClient(settings)
response = client.ask("What is machine learning?")
print(response)
```

### Provider selection + base_url

```python
from ai_utilities import AiClient, AiSettings

# Custom endpoint
settings = AiSettings(
    provider="openai-compatible",
    base_url="https://api.example.com/v1",
    api_key="your-key",
    model="your-model"
)
client = AiClient(settings)
response = client.ask("Hello, custom provider!")
print(response)
```

## Caching

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

## Embeddings

```python
from ai_utilities import AiClient

client = AiClient()
texts = ["Hello world", "Goodbye world"]
embeddings = client.get_embeddings(texts)
print(f"Generated {len(embeddings)} embeddings")
print(f"Vector length: {len(embeddings[0])}")
```

## Files

**Prerequisites:** `pip install "ai-utilities[openai]"` and `OPENAI_API_KEY`

```python
from ai_utilities import AiClient

client = AiClient()

# Upload a file
uploaded = client.upload_file("reports/data.txt")
print(f"Uploaded: {uploaded.filename}")

# List files
files = client.list_files()
print(f"Total files: {len(files)}")
```

## Audio

**Prerequisites:** `pip install "ai-utilities[openai]"` and `OPENAI_API_KEY`

```python
from ai_utilities import AiClient, validate_audio_file

client = AiClient()

# Validate audio file
validate_audio_file("reports/recording.wav")

# Transcribe audio
result = client.transcribe_audio("reports/recording.wav")
print(f"Transcript: {result['text']}")
```

## Images

**Prerequisites:** `pip install "ai-utilities[openai]"` and `OPENAI_API_KEY`

```python
from ai_utilities import AiClient

client = AiClient()

# Generate image
image_bytes = client.generate_image("A simple red circle")
print(f"Generated {len(image_bytes)} bytes")

# Save to file
with open("reports/circle.png", "wb") as f:
    f.write(image_bytes)
```

## Knowledge

```python
from ai_utilities import AiClient

client = AiClient()

# Index some documents
client.index_knowledge("reports/")

# Ask with knowledge
response = client.ask_with_knowledge("What are the main findings?")
print(response)
```

## Usage & Metrics

```python
from ai_utilities import AiClient

client = AiClient()

# Make a request
client.ask("What is machine learning?")

# Print usage summary
client.print_usage_summary()

# Or get stats object
stats = client.get_usage_stats()
if stats:
    print(f"Total tokens: {stats.total_tokens}")
```

## Local Ollama Usage

**Prerequisites:** Local Ollama server running

```python
from ai_utilities import AiClient, AiSettings

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

- Examples use the stable v1.0.0 public API
- No error handling included for brevity
- All examples are production-ready with proper imports
- Environment variables are loaded automatically from `.env` if present
- Local providers require the respective server to be running
- See [README.md](../README.md) for overview and [cheat sheet](cheat_sheet.md) for quick reference
- For detailed feature documentation, see [files.md](files.md), [audio_processing.md](audio_processing.md), and other guides
