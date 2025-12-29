# AI Utilities

A Python library for AI model interaction with Pydantic configuration, clean architecture, and dynamic rate limit management.

## Quickstart

```bash
# Install
pip install ai-utilities

# Set API key
export AI_API_KEY="your-openai-key"

# Use in Python
python -c "
from ai_utilities import AiClient
client = AiClient()
print(client.ask('What is AI?'))
"
```

**Where to look next:**
- More examples → [`examples/`](examples/)
- Configuration reference → [Configuration](#configuration)
- API reference → Use `help(AiClient)` in Python
- Changelog → [GitHub Releases](https://github.com/audkus/ai_utilities/releases)

---

## Install

### Standard Install
```bash
pip install ai-utilities
```

### Development Install
```bash
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities
pip install -e ".[dev]"
```

---

## Configuration

### Environment Variables

| Variable | AiSettings Field | Type | Default | Description |
|----------|------------------|------|---------|-------------|
| `AI_API_KEY` | `api_key` | str | None | OpenAI API key |
| `AI_PROVIDER` | `provider` | str | "openai" | Provider name |
| `AI_MODEL` | `model` | str | "gpt-3.5-turbo" | Model name |
| `AI_TEMPERATURE` | `temperature` | float | 0.7 | Response randomness |
| `AI_BASE_URL` | `base_url` | str | None | Custom API endpoint |
| `AI_TIMEOUT` | `timeout` | int | 60 | Request timeout (seconds) |

### Configuration Precedence

`AiSettings` loads values in this order (highest to lowest priority):

1. Explicit `AiSettings(...)` parameters
2. Environment variables (`os.environ`)
3. `.env` file values (loaded via `pydantic-settings`)
4. Defaults

---

## Providers

### OpenAI (Default)
```python
from ai_utilities import AiClient
client = AiClient()  # Uses OpenAI by default
response = client.ask("Hello, world!")
```

### OpenAI-Compatible Providers

#### Ollama
```python
from ai_utilities import AiClient, AiSettings

settings = AiSettings(
    provider="openai_compatible",
    base_url="http://localhost:11434/v1",
    model="llama3.2"
)
client = AiClient(settings)
```

#### LM Studio
```python
settings = AiSettings(
    provider="openai_compatible", 
    base_url="http://localhost:1234/v1",
    model="your-model"
)
```

#### FastChat
```python
settings = AiSettings(
    provider="openai_compatible",
    base_url="http://localhost:8000/v1", 
    model="vicuna-7b-v1.5"
)
```

### Provider Capabilities

Legend:
- ✅ full support
- ⚠️ partial / best-effort (varies by provider/model; may require JSON repair)
- ❌ not supported

| Provider Type | Text | JSON | Async | Streaming |
|--------------|------|------|-------|-----------|
| OpenAI (native) | ✅ | ✅ | ✅ | ✅ |
| OpenAI-compatible cloud (Groq/Together/OpenRouter/etc.) | ✅ | ⚠️ | ✅ | ⚠️ |
| OpenAI-compatible local (Ollama/LM Studio/FastChat/Text-Gen-WebUI/etc.) | ✅ | ⚠️ | ✅ | ❌ |

**Notes:**
- "Async" means our AsyncAiClient concurrency (parallel calls), not streaming tokens.
- Streaming is provider-dependent and not available on Ollama (and most local OpenAI-compatible servers).

JSON and typed responses are guaranteed only when the underlying provider supports native JSON mode.
On OpenAI-compatible providers (especially local servers), JSON is best-effort and may require repair/validation.

---

## Core API

### Synchronous Client

```python
from ai_utilities import AiClient

client = AiClient()

# Basic text response
response = client.ask("What is AI?")

# JSON response (best-effort parsing)
data = client.ask("List 3 programming languages", return_format="json")

# Structured JSON with repair
data = client.ask_json("List 3 countries", max_repairs=1)

# Typed response with Pydantic model
from pydantic import BaseModel
class Country(BaseModel):
    name: str
    population: int

countries = client.ask_typed("List a country", Country)
```

### Asynchronous Client

```python
import asyncio
from ai_utilities import AsyncAiClient, AiSettings

async def main():
    settings = AiSettings(model="gpt-4")
    client = AsyncAiClient(settings)
    
    response = await client.ask("What is async programming?")
    print(response)

asyncio.run(main())
```

### Convenience Functions

```python
from ai_utilities import create_client

# Quick client creation
client = create_client(
    provider="openai_compatible",
    base_url="http://localhost:11434/v1",
    api_key="not-needed",
    model="llama3.2"
)
```

---

## Development

### Running Tests
```bash
pytest                    # All tests
pytest -m "not slow"     # Skip slow tests
```

### Code Quality
```bash
ruff check . --fix        # Lint and fix
ruff format .             # Format code
mypy src/                 # Type checking
```

### Project Structure
```
ai_utilities/
├── src/ai_utilities/     # Core library
├── tests/                # Test suite
├── examples/             # Usage examples
├── scripts/              # Utility tools
├── docs/                 # Documentation
└── pyproject.toml        # Package config
```

---

## Documentation & Links

- **Full Documentation** → [`docs/`](docs/)
- **Usage Examples** → [`examples/`](examples/)
- **Provider Setup** → [`docs/all-providers-guide.md`](docs/all-providers-guide.md)
- **Testing Guide** → [`docs/testing-setup.md`](docs/testing-setup.md)
- **GitHub Releases** → [Releases](https://github.com/audkus/ai_utilities/releases)
- **Issues & Discussions** → [GitHub](https://github.com/audkus/ai_utilities)
- **Contributing** → [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
