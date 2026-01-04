# AI Utilities

[![CI](https://github.com/audkus/ai_utilities/actions/workflows/ci.yml/badge.svg)](https://github.com/audkus/ai_utilities/actions/workflows/ci.yml)
[![PyPI version (pre)](https://img.shields.io/pypi/vpre/ai-utilities?cacheSeconds=300)](https://pypi.org/project/ai-utilities/)

A Python library for AI model interaction with Pydantic configuration, clean architecture, dynamic rate limit management, and enterprise-grade testing infrastructure.

## Why This Library Exists

- **Unified Interface** - Single API for multiple AI providers (OpenAI, Anthropic, local models)
- **Smart Caching** - Automatic response caching with namespace isolation and TTL support
- **Rate Limiting** - Built-in rate limit management prevents API throttling and cost overruns
- **Type Safety** - Full Pydantic integration with comprehensive mypy support
- **Enterprise Ready** - Production-tested with comprehensive error handling and monitoring

## 🆚 Compared to Using Provider SDK Directly

| Feature | Direct SDK | AI Utilities |
|---------|------------|--------------|
| **Multi-provider** | X Separate SDKs needed | Single interface |
| **Caching** | X Manual implementation | Built-in, automatic |
| **Rate Limits** | X Manual tracking | Automatic management |
| **Type Safety** | Basic types | Full Pydantic models |
| **Error Handling** | Provider-specific | Unified exceptions |
| **Configuration** | Environment variables | Pydantic settings |
| **Testing** | X Manual mocking | Test utilities included |

**Use AI Utilities when you need:**
- Production applications with multiple AI providers
- Cost control through intelligent caching and rate limiting
- Type safety and comprehensive error handling
- Enterprise features like monitoring and configuration management

**Use direct SDK when you need:**
- Maximum control over a single provider
- Access to provider-specific features
- Minimal dependencies for simple scripts

## 👥 Who Is It For?

- **Production Teams** building AI-powered applications with reliability requirements
- **Startups** needing cost control through intelligent caching and rate limiting
- **Enterprise Developers** requiring type safety, monitoring, and configuration management
- **Data Scientists** who want to experiment with multiple providers without learning different APIs
- **Teams** collaborating on AI projects with standardized error handling and logging

## Quickstart

```bash
# Install with provider support
pip install ai-utilities[openai]

# Set API key
export OPENAI_API_KEY="your-openai-key"
```

### Recommended Usage

```python
from ai_utilities import AiClient

# Create client with automatic caching
client = AiClient()

# Ask questions with intelligent caching
result = client.ask(
    "Explain quantum computing in simple terms",
    cache_namespace="learning"
)

print(result.text)

# Monitor usage automatically
print(f"Tokens used: {result.usage.total_tokens}")
```

**Key Benefits:**
- ✅ **Automatic caching** - Same question = instant response, no API cost
- ✅ **Rate limiting** - Never get throttled or surprised by costs
- ✅ **Type safety** - Full IDE support with autocomplete
- ✅ **Error handling** - Clear, actionable error messages

**Where to look next:**
- **Getting Started** → [`examples/getting_started.py`](examples/getting_started.py) - **Recommended starting point**
- **Examples Guide** → [`examples/README.md`](examples/README.md) - Progressive learning path
- **Audio Processing Guide** → [`docs/audio_processing.md`](docs/audio_processing.md)
- Configuration reference → [Configuration](#configuration)
- **Error Handling Guide** → [`docs/error_handling.md`](docs/error_handling.md)
- **Smart Caching Guide** → [`docs/caching.md`](docs/caching.md)
- **Complete command reference** → [`docs/command_reference.md`](docs/command_reference.md)
- **Quick cheat sheet** → [`docs/cheat_sheet.md`](docs/cheat_sheet.md)
- **Test Dashboard** → [`docs/test_dashboard.md`](docs/test_dashboard.md)
- API reference → Use `help(AiClient)` in Python
- Changelog → [GitHub Releases](https://github.com/audkus/ai_utilities/releases)

---

## Why use ai_utilities?

This library is designed as a thin, opinionated utility layer for AI interactions. It is not a replacement for raw APIs, but rather provides consistent interfaces and common patterns for experimentation, testing, and long-term maintainability.

### Without ai_utilities

```python
# Direct API usage - provider-specific and repetitive
import openai

client = openai.OpenAI(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Explain AI"}],
    temperature=0.7,
    max_tokens=1000
)

# Manual error handling, no caching, no rate limiting
# Different API for each provider
# No structured JSON extraction
# No usage tracking
```

### With ai_utilities

```python
# Consistent interface across providers
from ai_utilities import AiClient

client = AiClient()  # Automatic configuration
response = client.ask("Explain AI")

# Built-in caching, rate limiting, error handling
# Same API for OpenAI, Anthropic, Ollama, etc.
# Structured JSON extraction included
# Usage tracking and monitoring
```

### Design Goals

ai_utilities is intended to provide:

- **Provider abstraction** - Switch between cloud and local models without code changes
- **Configuration management** - Environment-based settings with Pydantic validation
- **Test isolation** - Mock providers and deterministic testing patterns
- **Caching and rate limiting** - Built-in cost control and performance optimization
- **Error handling consistency** - Unified exception model across providers
- **JSON robustness** - Reliable structured output extraction with error recovery
- **Extensibility** - Designed for future multimodal and analytics features

### Design Intent

This library optimizes for development velocity and long-term maintainability rather than maximum feature access. It provides consistent patterns for common AI interaction tasks while allowing advanced users to access provider-specific capabilities through submodules when needed.

The approach is designed to support experimentation, testing, and production applications that benefit from:
- Unified interfaces across multiple providers
- Built-in testing utilities and mock providers
- Consistent error handling and logging
- Automatic caching and rate limiting
- Type safety and configuration validation

---

## Install

### Minimal Install
```bash
pip install ai-utilities
```
*Core library only - no provider SDKs included*

### With Provider Support
```bash
pip install ai-utilities[openai]
```
*Includes OpenAI SDK for provider functionality*

### Development Install
```bash
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities
pip install -e ".[dev]"
```

### With Audio Features
```bash
# Basic installation
pip install ai-utilities

# With audio processing capabilities
pip install ai-utilities[audio]

# Full installation with all features
pip install ai-utilities[all]
```

---

## API Stability (v1.x)

The following are considered stable public APIs and will follow semantic versioning:

- `AiClient` - Main client for AI interactions
- `AsyncAiClient` - Async version of AiClient  
- `AiSettings` - Configuration and settings
- `AskResult` - Response objects from AI requests

**Internal modules** (providers, cache backends, dashboards, scripts) may change in minor or patch releases unless explicitly documented otherwise.

**Version 1.x guarantees API stability**; new features may be added in minor releases.

**Semantic Versioning**: This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) - version 1.x maintains backward compatibility for stable APIs.

**Deprecation Policy**: Deprecated APIs will remain functional for at least one minor release and emit a warning before removal.

---

## Audio Processing

AI Utilities now includes comprehensive audio processing capabilities:

### Audio Transcription (OpenAI Whisper)
```python
from ai_utilities import AiClient

client = AiClient()
result = client.transcribe_audio("podcast.mp3")
print(f"Transcription: {result['text']}")
```

### Audio Generation (OpenAI TTS)
```python
# Generate speech from text
audio_data = client.generate_audio("Hello world!", voice="alloy")
with open("output.mp3", "wb") as f:
    f.write(audio_data)
```

### Audio Validation & Analysis
```python
# Validate audio files
validation = client.validate_audio_file("audio.wav")
print(f"Valid: {validation['valid']}")

# Extract metadata
from ai_utilities.audio.audio_utils import load_audio_file
audio_file = load_audio_file("music.mp3")
print(f"Duration: {audio_file.duration_seconds}s")
print(f"Metadata: {audio_file.metadata}")
```

### Format Conversion & Advanced Workflows
```python
from ai_utilities.audio.audio_utils import convert_audio_format
from ai_utilities.audio.audio_models import AudioFormat

# Convert between formats
convert_audio_format("input.wav", "output.mp3", AudioFormat.MP3)

# Complex workflows
from ai_utilities.audio import AudioProcessor
processor = AudioProcessor()
transcription, new_audio = processor.transcribe_and_generate(
    "speech.wav", target_voice="nova"
)
```

**Complete Audio Guide → [`docs/audio_processing.md`](docs/audio_processing.md)**

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

## 🧠 Smart Caching

AI Utilities includes intelligent caching with multiple backends to reduce API costs and improve response times.

### Quick Start

```python
from ai_utilities import AiClient, AiSettings
from pathlib import Path

# Enable memory caching
settings = AiSettings(
    cache_enabled=True,
    cache_backend="memory",
    cache_ttl_s=3600  # 1 hour
)
client = AiClient(settings=settings)

# First call hits the API
response1 = client.ask("What is machine learning?")

# Second call hits the cache (instant, no API cost)
response2 = client.ask("What is machine learning?")
```

### Cache Backends

| Backend | Persistence | Speed | Use Case |
|---------|-------------|-------|----------|
| **null** | None | Fastest | Testing, fresh responses |
| **memory** | Process lifetime | Fast | Development, short-lived apps |
| **sqlite** | Persistent | Medium | Production, long-running apps |

### SQLite Cache with Namespaces

```python
settings = AiSettings(
    cache_enabled=True,
    cache_backend="sqlite",
    cache_sqlite_path=Path.home() / ".ai_utilities" / "cache.sqlite",
    cache_namespace="my-project",  # Isolates cache per project
    cache_ttl_s=3600,
    cache_sqlite_max_entries=1000
)
client = AiClient(settings=settings)
```

**Key Features:**
- **Namespace isolation** - Prevents cross-project cache pollution
- **TTL expiration** - Automatic cleanup of stale entries
- **LRU eviction** - Memory-efficient size management
- **Thread-safe** - Concurrent access support
- **Persistent** - Survives process restarts

[📖 **Complete Caching Guide** → `docs/caching.md`](docs/caching.md)

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
- full support
- partial / best-effort (varies by provider/model; may require JSON repair)
- X not supported

| Provider Type | Text | JSON | Async | Streaming |
|--------------|------|------|-------|-----------|
| OpenAI (native) | full | full | full | full |
| OpenAI-compatible cloud (Groq/Together/OpenRouter/etc.) | full | partial | full | partial |
| OpenAI-compatible local (Ollama/LM Studio/FastChat/Text-Gen-WebUI/etc.) | full | partial | full | X |

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
| **OpenAI** | full | full | Full support with all file types |
| **OpenAI-Compatible** | X | X | Raises capability errors |

**📖 Full Documentation:** See [`docs/files.md`](docs/files.md) for comprehensive Files API documentation.

---

## Development

### Releases & Publishing

Releases are published automatically to PyPI when version tags are pushed:

- **Trigger**: Push a tag matching `v*` (e.g., `v1.0.0`, `v1.0.0b1`)
- **Authentication**: Uses PyPI Trusted Publishing (OIDC) - no secrets stored in GitHub
- **Supports**: Both stable releases and pre-releases (beta, alpha, release candidate)

Example release workflow:
```bash
git tag -a v1.0.0b1 -m "Release v1.0.0b1"
git push origin v1.0.0b1
# GitHub Actions will automatically publish to PyPI
```

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

**Enterprise Features:**
- **Chunked Execution**: Individual file isolation prevents cascading failures
- **Resilient Timeouts**: Robust hang detection with stack dump capabilities
- **Complete Visibility**: Shows exactly which tests are excluded and why
- **Accurate Reporting**: Partial progress tracking (e.g., "342/448 runnable tests passed")

**Test Visibility Example:**
```
Test Discovery Summary:
   Total tests available: 524
   Integration tests: 46 (excluded by default)
   Dashboard tests: 30 (excluded to prevent self-reference)
   Tests to execute: 448
   Excluded tests: 76
```

**Debugging Features:**
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

### Test Architecture

The project uses a clean, resilient test architecture designed for enterprise reliability:

**Test Categories:**
- **Unit Tests** (447 tests): Core functionality, provider implementations, utilities
- **Integration Tests** (46 tests): Real API calls, requires `AI_API_KEY` 
- **Dashboard Tests** (30 tests): Self-validation of the dashboard runner
- **Total**: 523 tests with clear separation and purpose

**Test Isolation:**
- Dashboard excludes its own tests to prevent self-reference issues
- Integration tests excluded by default, opt-in via `--integration`
- Chunked execution prevents cascading failures from hanging files
- Environment variable isolation prevents test interference

**Resilience Features:**
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

## Documentation & Links

- **Full Documentation** → [`docs/`](docs/)
- **Support & Maintenance** → [`SUPPORT.md`](SUPPORT.md)
- **Reliability Guide** → [`docs/reliability_guide.md`](docs/reliability_guide.md)
- **Security Guide** → [`docs/security_guide.md`](docs/security_guide.md)
- **Migration Guide** → [`MIGRATION.md`](MIGRATION.md)
- **Usage Examples** → [`examples/`](examples/)
- **Provider Setup** → [`docs/all-providers-guide.md`](docs/all-providers-guide.md)
- **Testing Guide** → [`docs/testing-setup.md`](docs/testing-setup.md)
- **Troubleshooting** → [`docs/provider_troubleshooting.md`](docs/provider_troubleshooting.md)
- **GitHub Releases** → [Releases](https://github.com/audkus/ai_utilities/releases)
- **Issues & Discussions** → [GitHub](https://github.com/audkus/ai_utilities)
- **Contributing** → [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Continuous Integration & Testing

### CI Pipeline Tiers

**Required Tier (Blocks Pull Requests)**
- Unit tests across Python 3.9-3.12
- Type checking with mypy
- Code linting with flake8
- Minimal installation verification

**Optional Tier (Informational Only)**
- Integration tests (requires API keys)
- Security scanning with safety and bandit
- Cross-platform compatibility tests
- Documentation validation
- Performance benchmarks

### What CI Guarantees

For v1.x releases, CI guarantees:
- All unit tests pass
- Type checking passes
- Code follows style guidelines
- Package installs correctly
- No breaking changes to public API

### What Is Informational

The following are monitored but do not block releases:
- External provider availability (provider health checks)
- Performance benchmarks (for regression detection)
- Security scan results (for awareness)
- Integration test results (depends on API keys)

### Running Tests Locally

```bash
# Required tests (what CI checks)
pytest tests/ -m "not integration and not dashboard"

# All tests including integration
pytest tests/ -m "not dashboard"

# Performance benchmarks (optional)
python tools/benchmarks.py
```

---

## Manual Verification (Pre-Release)

For pre-release verification, AI Utilities includes a comprehensive manual testing harness:

### Quick Start
```bash
# Run Tier 1 tests (all providers, no network required)
./manual_tests/run_manual_tests.sh

# Run Tier 1 + Tier 2 tests (OpenAI with real API calls)
export AI_API_KEY="your-openai-key"
./manual_tests/run_manual_tests.sh --tier2
```

### Test Tiers
- **Tier 1:** Validates all provider configurations without network access
- **Tier 2:** End-to-end testing with real API calls (OpenAI only by default)

For detailed instructions and release criteria, see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
