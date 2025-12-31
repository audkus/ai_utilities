# AI Utilities

A Python library for AI model interaction with Pydantic configuration, clean architecture, dynamic rate limit management, and enterprise-grade testing infrastructure.

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

**Or create a Python file:**
```python
# quickstart.py
from ai_utilities import AiClient

client = AiClient()
response = client.ask("What is AI?")
print(response)
```

**Where to look next:**
- More examples → [`examples/`](examples/)
- Configuration reference → [Configuration](#configuration)
- **Complete command reference** → [`docs/command_reference.md`](docs/command_reference.md)
- **Quick cheat sheet** → [`docs/cheat_sheet.md`](docs/cheat_sheet.md)
- **Test Dashboard** → [`docs/test_dashboard.md`](docs/test_dashboard.md)
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
| `AI_MODEL` | `model` | str | "test-model-1" | Default model to use |
| `AI_TEMPERATURE` | `temperature` | float | 0.7 | Response randomness (0.0-2.0) |
| `AI_BASE_URL` | `base_url` | str | None | Custom API endpoint |
| `AI_TIMEOUT` | `timeout` | int | 30 | Request timeout (seconds) |

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
    api_key="dummy-key",  # Optional for local servers
    model="llama3.2"
)
client = AiClient(settings)
```

#### LM Studio
```python
settings = AiSettings(
    provider="openai_compatible", 
    base_url="http://localhost:1234/v1",
    api_key="dummy-key",  # Optional for local servers
    model="your-model"
)
```

#### FastChat
```python
settings = AiSettings(
    provider="openai_compatible",
    base_url="http://localhost:8000/v1", 
    api_key="dummy-key",  # Optional for local servers
    model="vicuna-7b-v1.5"
)
```

**Note:** `api_key` is optional for local servers but required for cloud providers.

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
    api_key="dummy-key",
    model="llama3.2"
)
```

## Files API

Upload and download files through AI providers. Currently supported by OpenAI provider.

### Quick Start

```python
from ai_utilities import AiClient
from pathlib import Path

client = AiClient()

# Upload a file
file = client.upload_file("document.pdf", purpose="assistants")
print(f"Uploaded: {file.file_id}")

# Download file content
content = client.download_file(file.file_id)

# Download file to disk
path = client.download_file(file.file_id, to_path="downloaded.pdf")
```

### File Operations

```python
# Upload with custom settings
file = client.upload_file(
    "data.csv",
    purpose="fine-tune",
    filename="training-data.csv"
)

# Async file operations
from ai_utilities import AsyncAiClient

async def main():
    client = AsyncAiClient()
    file = await client.upload_file("document.pdf")
    content = await client.download_file(file.file_id)

# Error handling
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError

try:
    file = client.upload_file("report.pdf")
except FileTransferError as e:
    print(f"Upload failed: {e}")
except ProviderCapabilityError as e:
    print(f"Provider doesn't support files: {e}")
```

### Document AI Workflow

Upload documents and ask AI to analyze, summarize, or extract information:

```python
# 1. Upload document
client = AiClient()
uploaded_file = client.upload_file("report.pdf", purpose="assistants")

# 2. Ask AI to analyze the document
summary = client.ask(
    f"Please summarize document {uploaded_file.file_id} and extract key insights."
)

# 3. Ask follow-up questions
recommendations = client.ask(
    f"Based on document {uploaded_file.file_id}, what are your recommendations?"
)

# 4. Analyze multiple documents
docs = [
    client.upload_file("q1_report.pdf", purpose="assistants"),
    client.upload_file("q2_report.pdf", purpose="assistants")
]

trend_analysis = client.ask(
    f"Compare these reports: {[d.file_id for d in docs]}. "
    "Identify trends and key changes."
)
```

### Supported Providers

| Provider | Upload | Download | Notes |
|----------|--------|----------|-------|
| **OpenAI** | ✅ | ✅ | Full support with all file types |
| **OpenAI-Compatible** | ❌ | ❌ | Raises capability errors |

**📖 Full Documentation:** See [`docs/files.md`](docs/files.md) for comprehensive Files API documentation.

---

## Development

### Running Tests

#### 🧪 Enhanced Test Dashboard (Recommended)

The AI Utilities Test Dashboard provides enterprise-grade testing with resilience, debugging, and comprehensive visibility.

```bash
# Standard test suite (excludes integration & dashboard tests)
python scripts/dashboard.py

# With integration tests (requires API key)
python scripts/dashboard.py --integration

# Complete project test suite with chunked execution
python scripts/dashboard.py --full-suite

# Full suite with integration tests
python scripts/dashboard.py --full-suite --integration

# Enhanced debugging for hangs
python scripts/dashboard.py --full-suite --debug-hangs

# Custom timeout settings
python scripts/dashboard.py --full-suite --suite-timeout-seconds 600 --no-output-timeout-seconds 120
```

**🚀 Enterprise Features:**
- ✅ **Chunked Execution**: Individual file isolation prevents cascading failures
- ✅ **Resilient Timeouts**: Robust hang detection with stack dump capabilities
- ✅ **Complete Visibility**: Shows exactly which tests are excluded and why
- ✅ **Accurate Reporting**: Partial progress tracking (e.g., "342/448 runnable tests passed")
- ✅ **Self-Reference Prevention**: Dashboard tests excluded to avoid circular execution
- ✅ **Real-time Progress**: Live test execution with per-file granularity
- ✅ **Provider Coverage**: Analysis across 9 AI providers
- ✅ **Production Readiness**: Clear assessment and failure diagnostics

**📊 Test Visibility Example:**
```
📊 Test Discovery Summary:
   📋 Total tests available: 524
   🔧 Integration tests: 46 (excluded by default)
   🎛️  Dashboard tests: 30 (excluded to prevent self-reference)
   ✅ Tests to execute: 448
   📉 Excluded tests: 76
```

**🔧 Debugging Features:**
- `--debug-hangs`: Enable SIGQUIT stack dumps and verbose pytest output
- `--suite-timeout-seconds`: Hard timeout for entire test suite
- `--no-output-timeout-seconds`: Timeout if no output received
- Continues execution even when individual files hang
- Detailed diagnostics with last test nodeid and output tail

#### Standard Pytest
```bash
pytest                    # All tests (524 total)
pytest -m "not integration and not dashboard"  # Same as dashboard default
pytest -m integration     # Integration tests only (requires API key)
pytest -m dashboard       # Dashboard self-tests only
pytest tests/test_files_api.py  # Specific test files
```

### Code Quality
```bash
ruff check . --fix        # Lint and fix
ruff format .             # Format code
mypy src/                 # Type checking
```

### 🏗️ Test Architecture

The project uses a clean, resilient test architecture designed for enterprise reliability:

**📋 Test Categories:**
- **Unit Tests** (447 tests): Core functionality, provider implementations, utilities
- **Integration Tests** (46 tests): Real API calls, requires `AI_API_KEY` 
- **Dashboard Tests** (30 tests): Self-validation of the dashboard runner
- **Total**: 523 tests with clear separation and purpose

**🔒 Test Isolation:**
- Dashboard excludes its own tests to prevent self-reference issues
- Integration tests excluded by default, opt-in via `--integration`
- Chunked execution prevents cascading failures from hanging files
- Environment variable isolation prevents test interference

**🚀 Resilience Features:**
- Individual file timeouts prevent suite-wide hangs
- Stack dump capabilities for debugging hanging tests
- Partial progress reporting shows accurate completion status
- Continues execution even when individual files fail

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
