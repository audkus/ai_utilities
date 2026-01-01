# AI Utilities Cheat Sheet

Quick reference for the most commonly used commands and methods.

## Quick Setup

```python
from ai_utilities import AiClient, AsyncAiClient

# Sync client
client = AiClient()

# Async client
async_client = AsyncAiClient()
```

---

## Text Generation

### Basic
```python
response = client.ask("What is AI?")
data = client.ask("List 3 models", return_format="json")
```

### Advanced
```python
response = client.ask(
    "Explain quantum computing",
    temperature=0.7,
    max_tokens=500
)

# Batch
responses = client.ask_many(["Q1", "Q2", "Q3"])
```

---

## 🎵 Audio Processing

### Transcription
```python
# Basic transcription
result = client.transcribe_audio("audio.wav")
print(result['text'])

# With options
result = client.transcribe_audio(
    "podcast.mp3",
    language="en",
    temperature=0.1
)
```

### Audio Generation
```python
# Generate speech
audio_data = client.generate_audio("Hello world!", voice="alloy")
with open("output.mp3", "wb") as f:
    f.write(audio_data)

# With different voice and speed
audio_data = client.generate_audio(
    "Welcome!",
    voice="nova",
    speed=1.2
)
```

### Audio Validation
```python
# Validate audio file
validation = client.validate_audio_file("audio.wav")
if validation['valid']:
    print(f"Duration: {validation['file_info']['duration_seconds']}s")
```

### Voices
```python
# List available voices
voices = client.get_audio_voices()
# alloy, echo, fable, onyx, nova, shimmer
```

### Advanced Audio
```python
from ai_utilities.audio import AudioProcessor
from ai_utilities.audio.audio_utils import convert_audio_format

# Load with metadata
audio_file = load_audio_file("music.mp3")
print(f"Metadata: {audio_file.metadata}")

# Convert format
convert_audio_format("input.wav", "output.mp3", "mp3")

# Complex workflow
processor = AudioProcessor()
transcription, new_audio = processor.transcribe_and_generate(
    "speech.wav", target_voice="nova"
)
```

---

## Files API - Document Operations

### Upload & Analyze
```python
# Upload document
doc = client.upload_file("report.pdf", purpose="assistants")

# Analyze document
summary = client.ask(f"Summarize {doc.file_id}")
insights = client.ask(f"Extract insights from {doc.file_id}")
```

### Download
```python
# Download as bytes
content = client.download_file("file-abc123")

# Download to file
path = client.download_file("file-abc123", to_path="saved.pdf")
```

### Multi-Document
```python
docs = [
    client.upload_file("q1.pdf", purpose="assistants"),
    client.upload_file("q2.pdf", purpose="assistants")
]

comparison = client.ask(
    f"Compare {[d.file_id for d in docs]} and identify trends"
)
```

---

## Image Generation

### Basic
```python
# Generate image
urls = client.generate_image("A cute dog playing fetch")
image_url = urls[0]
```

### Advanced
```python
# Multiple high-quality images
urls = client.generate_image(
    "A majestic landscape",
    size="1792x1024",    # Wide format
    quality="hd",        # High quality
    n=3                  # 3 variations
)
```

### Download Image
```python
import requests

response = requests.get(urls[0])
with open("image.png", "wb") as f:
    f.write(response.content)
```

---

## Async Operations

```python
import asyncio

async def main():
    client = AsyncAiClient()
    
    # Concurrent requests
    tasks = [
        client.ask("What is Python?"),
        client.generate_image("A cat"),
        client.upload_file("doc.pdf")
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Run
results = asyncio.run(main())
```

---

## Error Handling

```python
from ai_utilities.providers.provider_exceptions import (
    FileTransferError,
    ProviderCapabilityError
)

try:
    images = client.generate_image("A dog")
except ProviderCapabilityError as e:
    print(f"Provider doesn't support: {e.capability}")
except FileTransferError as e:
    print(f"Operation failed: {e}")
```

---

## Configuration

### Environment Variables
```bash
export AI_API_KEY="your-key"
export AI_MODEL="gpt-4"
export AI_BASE_URL="http://localhost:11434/v1"
```

### Programmatic
```python
from ai_utilities import AiClient, create_client

# Quick creation
client = create_client(
    provider="openai_compatible",
    base_url="http://localhost:11434/v1",
    model="llama3.2"
)

# Custom provider
from ai_utilities.providers import OpenAICompatibleProvider
provider = OpenAICompatibleProvider(base_url="http://localhost:11434/v1")
client = AiClient(provider=provider)
```

---

## Common Workflows

### Document Analysis
```python
# 1. Upload
doc = client.upload_file("financial_report.pdf")

# 2. Analyze
summary = client.ask(f"Summarize {doc.file_id}")
metrics = client.ask(f"Extract metrics from {doc.file_id}")

# 3. Recommendations
recommendations = client.ask(f"Recommendations based on {doc.file_id}")
```

### Content Creation
```python
# 1. Generate text
content = client.ask("Write about remote work")

# 2. Generate images
images = client.generate_image(
    "Remote workspace setup",
    size="1792x1024",
    n=2
)

# 3. Social media
social = client.ask("Create LinkedIn post about remote work")
```

### Batch Processing
```python
# Process multiple documents
docs = [client.upload_file(f) for f in file_list]
analyses = [client.ask(f"Analyze {d.file_id}") for d in docs]
summary = client.ask(f"Summarize: {' '.join(analyses)}")
```

---

## Parameters Reference

### Text Generation
- `temperature`: 0.0-2.0 (creativity)
- `max_tokens`: response length
- `top_p`: nucleus sampling
- `frequency_penalty`: -2.0 to 2.0
- `presence_penalty`: -2.0 to 2.0

### Image Generation
- `size`: "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
- `quality`: "standard", "hd"
- `n`: 1-10 (number of images)

### File Upload
- `purpose`: "assistants", "fine-tune"
- `filename`: custom filename
- `mime_type`: MIME type

---

## Provider Support

| Feature | OpenAI | OpenAI-Compatible |
|---------|--------|-------------------|
| Text Generation | ✅ | ✅ |
| Image Generation | ✅ | ❌ |
| File Upload | ✅ | ❌ |
| File Download | ✅ | ❌ |

---

## Quick Examples

### Blog Post with Images
```python
# Generate content
content = client.ask("Write about sustainable technology")

# Generate illustrations
images = client.generate_image(
    "Sustainable technology concept",
    size="1792x1024",
    n=3
)

# Complete package
blog = {
    'content': content,
    'images': images
}
```

### Document Analysis
```python
# Upload and analyze
doc = client.upload_file("contract.pdf")
summary = client.ask(f"Summarize {doc.file_id}")
risks = client.ask(f"Identify risks in {doc.file_id}")
```

### Async Content Creation
```python
async def create_content():
    client = AsyncAiClient()
    
    content, images = await asyncio.gather(
        client.ask("Write about AI ethics"),
        client.generate_image("AI ethics concept", n=2)
    )
    
    return {'content': content, 'images': images}
```

---

## One-Liners

```python
# Quick question
answer = client.ask("What is machine learning?")

# Generate image
url = client.generate_image("A sunset")[0]

# Upload and analyze
doc = client.upload_file("report.pdf")
summary = client.ask(f"Summarize {doc.file_id}")

# Batch analysis
results = client.ask_many(["Q1", "Q2", "Q3"])
```

---

**Save this cheat sheet for quick reference when building with ai_utilities!** 🚀
