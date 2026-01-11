# Provider Setup

## Supported Providers

### OpenAI (Default)

**Setup:**
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
AI_MODEL=gpt-3.5-turbo
```

**Models:**
- `gpt-4` - Most capable, higher cost
- `gpt-3.5-turbo` - Fast, cost-effective
- `gpt-4-turbo` - Balanced performance

**Features:**
- Text generation
- Function calling
- JSON mode
- Streaming responses

### Groq

**Setup:**
```bash
AI_PROVIDER=groq
AI_API_KEY=gsk_your-groq-key
AI_MODEL=llama3-70b-8192
```

**Models:**
- `llama3-70b-8192` - High performance
- `llama3-8b-8192` - Fast, cost-effective
- `mixtral-8x7b-32768` - Good for reasoning

**Features:**
- Very fast inference
- Open source models
- Lower cost than OpenAI

### Together AI

**Setup:**
```bash
AI_PROVIDER=together
AI_API_KEY=your-together-key
AI_MODEL=meta-llama/Llama-3-8b-chat-hf
```

**Models:**
- `meta-llama/Llama-3-8b-chat-hf`
- `meta-llama/Llama-3-70b-chat-hf`
- `mistralai/Mixtral-8x7B-Instruct-v0.1`

**Features:**
- Wide model selection
- Open source models
- Competitive pricing

### OpenRouter

**Setup:**
```bash
AI_PROVIDER=openrouter
AI_API_KEY=sk-or-your-openrouter-key
AI_MODEL=meta-llama/llama-3-8b-instruct:free
```

**Models:**
- `meta-llama/llama-3-8b-instruct:free`
- `anthropic/claude-3-haiku`
- `openai/gpt-4o-mini`

**Features:**
- Access to multiple providers
- Free tier available
- Unified billing

### Ollama (Local)

**Setup:**
```bash
AI_PROVIDER=ollama
AI_MODEL=llama3
AI_BASE_URL=http://localhost:11434/v1
```

**Models:**
- `llama3`
- `codellama`
- `mistral`
- Custom models

**Features:**
- Local inference
- No API costs
- Privacy-focused
- Requires local setup

### OpenAI-Compatible (Custom)

**Setup:**
```bash
AI_PROVIDER=openai_compatible
AI_API_KEY=your-custom-key
AI_MODEL=your-custom-model
AI_BASE_URL=https://your-endpoint.com/v1
```

**Use Cases:**
- Custom model deployments
- Private cloud deployments
- Specialized AI services
- Development/testing

## Audio Processing

### OpenAI Audio

**Setup:**
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key
```

**Transcription:**
```python
from ai_utilities import AiClient

client = AiClient()

# Transcribe audio file
with open("audio.mp3", "rb") as f:
    transcript = client.transcribe(f)
    print(transcript.text)
```

**Generation:**
```python
# Generate speech
audio_data = client.generate_speech(
    "Hello, world!",
    voice="alloy",
    model="tts-1"
)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_data)
```

**Supported Voices:**
- `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

## Provider Capabilities

| Provider | Text | Audio | Streaming | JSON Mode | Local |
|----------|------|-------|-----------|-----------|-------|
| OpenAI | ✓ | ✓ | ✓ | ✓ | ✗ |
| Groq | ✓ | ✗ | ✓ | ✗ | ✗ |
| Together AI | ✓ | ✗ | ✓ | ✗ | ✗ |
| OpenRouter | ✓ | ✗ | ✓ | ✗ | ✗ |
| Ollama | ✓ | ✗ | ✓ | ✗ | ✓ |
| OpenAI-Compatible | ✓ | Varies | Varies | Varies | Varies |

## Choosing a Provider

### For Production Use
- **OpenAI** - Most reliable, full features
- **Groq** - Fastest inference, good for real-time
- **Together AI** - Good balance of cost and performance

### For Development/Testing
- **Ollama** - No API costs, local privacy
- **OpenRouter** - Free tier available
- **Groq** - Fast iteration with low cost

### For Cost Optimization
- **Groq** - Lowest cost for high performance
- **Together AI** - Competitive pricing
- **Ollama** - No recurring costs

For configuration details, see [Configuration Guide](configuration.md).
