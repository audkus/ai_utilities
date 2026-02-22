# AI Utilities

[![PyPI version](https://img.shields.io/pypi/v/ai-utilities.svg)](https://pypi.org/project/ai-utilities/)
[![Python versions](https://img.shields.io/pypi/pyversions/ai-utilities.svg)](https://pypi.org/project/ai-utilities/)
[![CI status](https://github.com/audkus/ai_utilities/workflows/CI/badge.svg)](https://github.com/audkus/ai_utilities/actions)
[![Code coverage](https://codecov.io/gh/audkus/ai_utilities/branch/main/graph/badge.svg)](https://codecov.io/gh/audkus/ai_utilities)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for AI model interaction with unified interface, intelligent caching, and type safety. Use OpenAI, Groq, Together AI, Ollama, and other providers with the same code.

<!-- CI trigger check -->

## Minimal usage (copy & paste)

These examples work without cloning the repository and represent the simplest possible usage.

### Basic question

```bash
pip install ai-utilities[openai]
export OPENAI_API_KEY="your-api-key"
```

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("What is the capital of France?")
print(response)
```

### With environment variable

```bash
pip install ai-utilities[openai]
export AI_API_KEY="your-api-key"
export AI_MODEL="gpt-4o-mini"
```

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("Explain photosynthesis in one sentence")
print(response)
```

### Async version

```bash
pip install ai-utilities[openai]
export OPENAI_API_KEY="your-api-key"
```

```python
from ai_utilities import AsyncAiClient
import asyncio

async def main():
    client = AsyncAiClient()
    response = await client.ask("What is 2+2?")
    print(response)

asyncio.run(main())
```

## Who This Is For

AI Utilities is for developers who need to integrate AI capabilities into their applications without being locked into a single provider. It's designed for both beginners who want simple AI interactions and advanced users who need production-ready features like caching and rate limiting.

## What Problem It Solves

Managing multiple AI providers is complex and error-prone. Each provider has different APIs, authentication methods, and error handling. AI Utilities solves this by providing a single, consistent interface that works across all major providers while adding enterprise features like intelligent caching and comprehensive error handling.

## Quickstart

### Install

```bash
pip install ai-utilities[openai]
```

### Quick Setup (Recommended)

Run the interactive setup wizard to configure your provider:

```bash
ai-utilities setup
```

The setup wizard will:
- Guide you through provider selection (OpenAI, Groq, Ollama, etc.)
- Create or update your `.env` file with proper configuration
- Detect missing optional dependencies and provide install commands
- Support both single-provider and multi-provider auto-selection modes

**Setup modes:**
- **Single provider**: Configure one AI provider (e.g., just OpenAI)
- **Multi-provider**: Configure multiple providers with auto-selection
- **Non-interactive**: Use command-line flags for automation

**Examples:**
```bash
# Interactive setup (recommended)
ai-utilities setup

# Non-interactive single provider
ai-utilities setup --mode single-provider --provider ollama --model llama3.1

# Multi-provider with custom order
ai-utilities setup --mode multi-provider
```

The setup creates a `.env` file with provider-specific variables like:
```bash
# Single provider example
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1

# Multi-provider example  
AI_PROVIDER=auto
AI_AUTO_SELECT_ORDER=ollama,lmstudio,groq,openai
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1
GROQ_API_KEY=your-groq-key
OPENAI_API_KEY=your-openai-key
```

## 5-minute Tour

Get started immediately with these copy-pasteable examples. Each runs independently after setting environment variables.

### Minimal synchronous call

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("What is the capital of France?")
print(response)
```

### Error handling

```python
from ai_utilities import AiClient

client = AiClient()

try:
    client.ask("Hello")
except Exception as e:
    print(type(e).__name__, e)
```

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

### Two ways to configure providers

`ai-utilities` supports both **provider-specific environment variables** and a
**generic, provider-agnostic configuration**.

You can use either style — or mix them — depending on your preference.

#### Option A: Provider-specific variables (explicit)

```bash
# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Groq
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama3-70b-8192
```

This style is useful when tuning provider-specific behavior.

#### Option B: Generic AI_* variables (interchangeable)

```bash
AI_PROVIDER=openai
AI_API_KEY=your-openai-key
AI_MODEL=gpt-4o-mini
```

Switch providers without changing code:

```bash
AI_PROVIDER=groq
AI_API_KEY=your-groq-key
AI_MODEL=llama3-70b-8192
```

All examples in this README work unchanged with either configuration style.

#### Multi-provider setup (recommended)

```bash
# Auto-select first available provider
AI_PROVIDER=auto
AI_AUTO_SELECT_ORDER=openai,groq,openrouter,together

# Configure multiple providers simultaneously
OPENAI_API_KEY=sk-your-openai-key
GROQ_API_KEY=gsk-your-groq-key
```

No code changes are required when switching providers - ai_utilities will 
automatically use the first available provider based on your keys.

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

### Provider selection

```python
from ai_utilities import AiClient, AiSettings

# Explicit provider selection
settings = AiSettings(provider="groq", api_key="your-key", model="llama3-70b-8192")
client = AiClient(settings)
response = client.ask("What is machine learning?")
print(response)
```

Programmatic `AiSettings(provider=...)` overrides environment auto-selection for that client instance only.

### Provider Auto-Selection (v1.0.1+)

When `AI_PROVIDER=auto` (default in v1.0.1+), the library automatically selects the first available provider based on:

1. **Custom order** (if `AI_AUTO_SELECT_ORDER` is set)
2. **Default order** (local providers first, then hosted)

**Default auto-selection order:**
```
ollama, lmstudio, groq, openrouter, together, deepseek, openai, fastchat, text-generation-webui
```

**Example configuration:**
```bash
# Auto-select with custom order
AI_PROVIDER=auto
AI_AUTO_SELECT_ORDER=ollama,groq,openai

# Configure multiple providers
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1
GROQ_API_KEY=your-groq-key
OPENAI_API_KEY=your-openai-key
```

**Behavior:**
- Tries providers in order until one is configured and accessible
- Local providers (Ollama, LM Studio) are tried before hosted providers by default
- Raises clear error if no providers are configured (no silent OpenAI fallback)
- Use `ai-utilities setup` to configure providers easily

### Structured JSON output

```python
from ai_utilities import AiClient, parse_json_from_text

client = AiClient()
response = client.ask("List 3 programming languages with their year created")
data = parse_json_from_text(response)
print(data)
```

### Caching behavior

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

### Local Ollama usage

Local providers behave exactly like cloud providers and can be configured
either via environment variables or programmatically.

#### Option A: Using .env (recommended)

```bash
AI_PROVIDER=ollama
AI_BASE_URL=http://localhost:11434/v1
AI_MODEL=llama3.1
```

Alternative: configure Ollama via .env with provider-specific variables:

```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1
# Either AI_PROVIDER=ollama OR AI_PROVIDER=auto with Ollama included in order
```

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("Hello, local model!")
print(response)
```

Both approaches are supported and interchangeable.

#### Option B: Programmatic configuration

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

### Embeddings

```python
from ai_utilities import AiClient

client = AiClient()
texts = ["Hello world", "Goodbye world"]
embeddings = client.get_embeddings(texts)
print(f"Generated {len(embeddings)} embeddings")
print(f"Vector length: {len(embeddings[0])}")
```

### Files (requires openai extra)

```python
from ai_utilities import AiClient

# Install: pip install "ai-utilities[openai]"
client = AiClient()

# Upload a file
uploaded = client.upload_file("reports/data.txt")
print(f"Uploaded: {uploaded.filename}")

# List files
files = client.list_files()
print(f"Total files: {len(files)}")
```

### Audio transcription (requires openai extra)

```python
from ai_utilities import AiClient, validate_audio_file

# Install: pip install "ai-utilities[openai]"
client = AiClient()

# Validate audio file
validate_audio_file("reports/recording.wav")

# Transcribe audio
result = client.transcribe_audio("reports/recording.wav")
print(f"Transcript: {result['text']}")
```

### Image generation (requires openai extra)

```python
from ai_utilities import AiClient

# Install: pip install "ai-utilities[openai]"
client = AiClient()

# Generate image
image_bytes = client.generate_image("A simple red circle")
print(f"Generated {len(image_bytes)} bytes")

# Save to file
with open("reports/circle.png", "wb") as f:
    f.write(image_bytes)
```

### Knowledge search

```python
from ai_utilities import AiClient

client = AiClient()

# Index documents (stored locally and reused across runs)
client.index_knowledge("reports/")

# Ask with knowledge
response = client.ask_with_knowledge("What are the main findings?")
print(response)
```

### Usage tracking

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

#### Sanity check

```bash
pip install ai-utilities[openai]
echo "OPENAI_API_KEY=your-key" > .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env

python demo.py  # Where demo.py contains any example above
```

The same example file can be reused across providers by changing only `.env`.
No code changes are required.

## Why Use AI Utilities

### Raw OpenAI SDK

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is the capital of France?"}]
)
print(response.choices[0].message.content)
```

### AI Utilities

```python
from ai_utilities import AiClient

client = AiClient()
response = client.ask("What is the capital of France?")
print(response)
```

**AI Utilities eliminates boilerplate** while adding unified provider support, intelligent caching, and comprehensive error handling.

For more examples, see [docs/examples/README.md](docs/examples/README.md) and the [cheat sheet](docs/cheat_sheet.md).

## Stability and support

### Supported Python versions
- Python 3.9+
- Tested on 3.9, 3.10, 3.11, 3.12

### Stable public API
The following APIs are considered stable and will not break without a major version bump:
- `AiClient` and `AsyncAiClient` classes
- `AiSettings` configuration
- Core methods: `ask()`, `ask_with_knowledge()`, `get_embeddings()`
- File operations: `upload_file()`, `download_file()`, `list_files()`
- Usage tracking: `get_usage_stats()`, `print_usage_summary()`

### Provider support
- **OpenAI**: Full support with all features
- **Groq, Together AI, OpenRouter**: Core text generation support
- **Local providers (Ollama, FastChat, etc.)**: Best-effort support for text generation
- **Advanced features** (JSON mode, streaming, tools): Provider-dependent

### Support boundaries
- Documentation errors and examples are fully supported
- Core functionality issues across supported providers are prioritized
- Provider-specific issues may be best-effort depending on provider stability
- Local provider support depends on the underlying server implementation

## Engineering Guarantees

This project is designed for stability and long-term reliability.

### Testing Depth

- **Extensive unit test coverage** across all public APIs and internal components
- **Integration tests** (opt-in, API-key based) validate real provider interactions
- **Contract tests** guard public APIs against undocumented breaking changes
- **CI validation** runs across multiple Python versions and environments
- **Documentation contract tests** ensure all README examples remain functional

### Stability Philosophy

- **Stable public API** with clearly marked compatibility exports
- **Breaking changes treated as bugs**, not normal evolution
- **Documentation examples treated as contracts**, not demos
- **Version stability** - v1.0.0 APIs are guaranteed to remain stable

### Operational Safety

- **Environment isolation** - integration tests opt-in via .env configuration
- **No repository pollution** - tests never write to project root
- **Project structure enforcement** prevents accidental file creation
- **Defensive programming** handles provider differences gracefully

### Provider Volatility Handling

- **Abstracted provider interfaces** isolate users from API changes
- **Centralized error handling** provides consistent behavior across providers
- **Graceful degradation** when providers change behavior
- **Auto-selection logic** tested across multiple provider configurations

### What Users Can Rely On

- **README examples continue to work** across minor and patch releases
- **Provider switching without code changes** through configuration
- **Predictable behavior** across development and production environments
- **Backward compatibility** for stable APIs within major versions
- **Bug fixes** for any breaking change to documented functionality

If a documented example breaks, it is considered a bug and will be fixed.

## Quickstart

### Stable Public API (v1.0.0)

The following classes and functions are **guaranteed to remain stable** across v1.0.0 releases:

#### ✅ Core Classes (Stable)
- `AiClient` - Main client class for AI interactions
- `AsyncAiClient` - Async client class
- `AiSettings` - Configuration settings
- `create_client()` - Client factory function

#### ✅ Response Types (Stable)
- `AskResult` - Response from AI requests
- `UploadedFile` - File upload result

#### ✅ Error Handling (Stable)
- `JsonParseError` - JSON parsing errors
- `parse_json_from_text()` - JSON parsing utility

#### ✅ Audio Processing (Stable)
- `AudioProcessor` - Audio file processing
- `load_audio_file()` - Load audio files
- `save_audio_file()` - Save audio files
- `validate_audio_file()` - Validate audio files
- `get_audio_info()` - Get audio file information

### 📦 Compatibility Exports (May Change)

The following are available for backwards compatibility but **may change** in future releases:

#### ⚠️ Usage Tracking (Compatibility)
- `UsageTracker*` - Usage tracking classes
- `create_usage_tracker()` - Usage tracker factory

#### ⚠️ Rate Limiting (Compatibility)
- `RateLimitFetcher` - Rate limit information
- `RateLimitInfo` - Rate limit data

#### ⚠️ Token Counting (Compatibility)
- `TokenCounter` - Token counting utilities

#### ⚠️ Provider Classes (Compatibility)
- `BaseProvider` - Base provider class
- `OpenAIProvider` - OpenAI provider
- `create_provider()` - Provider factory
- Other provider-specific classes

#### ⚠️ Audio Models (Compatibility)
- `AudioFormat` - Audio format enums
- `TranscriptionRequest` - Transcription request
- Other audio model classes

### 🔄 Migration Path

For new development, prefer the stable API:

```python
# ✅ Recommended (Stable API)
from ai_utilities import AiClient, AiSettings
client = AiClient()

# ⚠️ Legacy (Compatibility API)
from ai_utilities import UsageTracker, create_usage_tracker
# Consider using ai_utilities.usage in future versions
```

### 📋 What This Means for Developers

- **✅ Safe to use**: All stable API classes will work without breaking changes
- **⚠️ May change**: Compatibility exports might be modified or moved in future releases
- **🔄 Migration plan**: Compatibility exports will be available but gradually deprecated
- **📚 Documentation**: Always check the stable API list above for guaranteed interfaces

## Common Usage Examples

### With Caching

```python
from ai_utilities import AiClient

client = AiClient()

# What is caching?
# Caching stores AI responses locally so identical questions 
# get instant answers without API calls or costs.

# Ask questions with intelligent caching
result = client.ask(
    "Explain quantum computing in simple terms",
    cache_namespace="learning"  # Groups related cached responses
)

print(result.text)

# First call: Hits API, costs tokens, stores response
# Second call (same question): Instant response, $0 cost
```

### Different Providers

```python
from ai_utilities import AiClient, AiSettings

# Use Groq instead of OpenAI
settings = AiSettings(
    provider="groq",
    api_key="your-groq-key",
    model="llama3-70b-8192"
)

client = AiClient(settings)
response = client.ask("What is machine learning?")
```

### Async Usage

```python
import asyncio
from ai_utilities import AsyncAiClient

async def main():
    client = AsyncAiClient()
    response = await client.ask("Hello, world!")
    print(response)

asyncio.run(main())
```

## Metrics and Monitoring

AI Utilities provides comprehensive metrics collection and monitoring capabilities for production use cases. Track performance, usage, and latency across all AI providers.

### Basic Metrics Collection

```python
from ai_utilities.metrics import MetricsCollector

# Create a metrics collector
collector = MetricsCollector()

# Record different types of metrics
collector.increment_counter("api_requests", labels={"provider": "openai"})
collector.set_gauge("active_connections", 5, labels={"service": "ai-api"})
collector.observe_histogram("response_time", 1.5, labels={"endpoint": "/chat"})
collector.record_timer("request_latency", 0.8, labels={"model": "gpt-4"})

# Get all metrics for monitoring
all_metrics = collector.get_all_metrics()
for metric in all_metrics:
    print(f"{metric.name}: {metric.value} ({metric.metric_type})")
```

### Timer Metrics for Latency Tracking

Timer metrics automatically generate comprehensive latency snapshots:

```python
from ai_utilities.metrics import MetricsCollector

collector = MetricsCollector()

# Record timer values (perfect for latency tracking)
collector.record_timer("api_latency", 1.2, labels={"endpoint": "/chat"})
collector.record_timer("api_latency", 0.8, labels={"endpoint": "/chat"})
collector.record_timer("api_latency", 1.5, labels={"endpoint": "/chat"})

# Timer snapshots are automatically exported as 5 metrics:
# - api_latency_count: 3 (number of events)
# - api_latency_sum_seconds: 3.5 (total duration)
# - api_latency_min_seconds: 0.8 (minimum duration)
# - api_latency_max_seconds: 1.5 (maximum duration)
# - api_latency_last_seconds: 1.5 (last duration)

metrics = collector.get_all_metrics()
timer_metrics = {m.name: m.value for m in metrics if "api_latency" in m.name}
print(timer_metrics)
```

### Export Metrics to Monitoring Systems

```python
from ai_utilities.metrics import MetricsCollector, PrometheusExporter, JSONExporter

collector = MetricsCollector()
# ... record metrics ...

# Prometheus format (perfect for Grafana/Prometheus)
prometheus_exporter = PrometheusExporter(collector)
prometheus_output = prometheus_exporter.export()
print(prometheus_output)

# JSON format (perfect for APIs and dashboards)
json_exporter = JSONExporter(collector)
json_output = json_exporter.export()
print(json_output)
```

### Context Manager for Easy Timing

```python
from ai_utilities.metrics import MetricsCollector

collector = MetricsCollector()

# Use context manager for automatic timing
with collector.timer("database_query", labels={"table": "users"}):
    # Your code here - automatically timed
    result = some_database_operation()

# Timer automatically records the duration
```

### Available Metric Types

- **Counters**: Incrementing values (request counts, error counts)
- **Gauges**: Current values (active connections, memory usage)
- **Histograms**: Value distributions (response times)
- **Timers**: Duration tracking with automatic statistics (latency, processing time)

### Integration with AI Clients

```python
from ai_utilities import AiClient
from ai_utilities.metrics import MetricsCollector, PrometheusExporter

# Set up metrics collection
collector = MetricsCollector()

# Monitor AI client usage
client = AiClient()

# Manually track usage
collector.increment_counter("ai_requests", labels={"provider": "openai"})
collector.record_timer("ai_response_time", 2.1, labels={"model": "gpt-4"})

response = client.ask("What is machine learning?")

# Export for monitoring
exporter = PrometheusExporter(collector)
print(exporter.export())
```

## Supported Providers

- **OpenAI** - GPT-4, GPT-4o-mini, audio processing
- **Groq** - Fast inference with Llama models
- **Together AI** - Open source models
- **OpenRouter** - Multiple model access
- **Ollama** - Local server support
- **OpenAI Compatible** - Custom endpoints

## Troubleshooting

### SSL Backend Requirements

ai_utilities requires OpenSSL ≥ 1.1.1 for reliable HTTPS operations. Some macOS Python installations use LibreSSL, which is unsupported by urllib3 v2 (used by requests).

**Symptoms:**
- HTTPS requests may fail unexpectedly
- Warning: `NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+`
- Warning: `SSLBackendCompatibilityWarning: SSL Backend Compatibility Notice: Detected LibreSSL`

**Check your SSL backend:**
```python
import ssl
print(ssl.OPENSSL_VERSION)
```

**Fixes:**
- Use Python from python.org (recommended)
- Install via Homebrew: `brew install python`
- Use pyenv: `pyenv install 3.11.0`
- Avoid system Python on macOS

**Why OpenSSL is required:**
- urllib3 v2 dropped LibreSSL support for security reasons
- HTTPS behavior may be unreliable with LibreSSL
- This is an environment compatibility notice, not a bug in ai_utilities
- Network functionality may be affected

**Filtering warnings in pytest:**
```bash
pytest -W "ignore::SSLBackendCompatibilityWarning"
```

### Top 5 Common Issues

1. **"API key is required"**
   ```bash
   ai-utilities setup
   # Or set: export AI_API_KEY=your-key
   ```

2. **"Provider not supported"**
   ```bash
   export AI_PROVIDER=openai  # Use lowercase name
   ```

3. **Network connection issues**
   ```bash
   # Check internet connection
   curl -I https://api.openai.com/v1/models
   ```

4. **Model not found**
   ```bash
   # Use correct model names:
   # OpenAI: gpt-4, gpt-4o-mini
   # Groq: llama3-70b-8192
   ```

5. **Caching not working**
   ```bash
   export AI_CACHE_ENABLED=true
export AI_CACHE_BACKEND=sqlite
```

## Testing

### Running Tests

This project uses pytest with timeout protection to prevent hanging tests.

#### Unit Tests (Fast, No .env Required)
```bash
# Run unit tests only (no external API calls, deterministic)
tox -e py311
# or
pytest -m "not integration" --timeout=30
```

#### Integration Tests (Requires API Keys, Opt-in .env Loading)

Integration tests require explicit opt-in to load `.env` files and need API keys:

```bash
# Option 1: Use tox with opt-in .env loading (recommended)
tox -e integration

# Option 2: Manual opt-in with environment variable
AI_UTILITIES_LOAD_DOTENV=1 pytest -m integration --timeout=120

# Option 3: Export API keys manually (alternative to .env)
export OPENAI_API_KEY=your-openai-key
export AI_OPENAI_API_KEY=your-alt-openai-key
pytest -m integration --timeout=120
```

**Key Points:**
- Unit tests never load `.env` files and remain deterministic
- Integration tests only load `.env` when `AI_UTILITIES_LOAD_DOTENV=1` is set
- Integration tests check both `OPENAI_API_KEY` and `AI_OPENAI_API_KEY` environment variables
- Use tox environments for consistent testing across Python versions

**Note**: Integration tests are automatically skipped if API keys are missing.

#### All Tests
```bash
# Run all tests with appropriate timeouts
pytest -m "not integration" --timeout=30  # Unit tests
pytest -m "integration" --timeout=120     # Integration tests (if API key available)
```

### Test Timeouts

- **Unit tests**: 30 seconds per test (fail fast)
- **Integration tests**: 120 seconds per test (allow for network latency)
- **Request timeouts**: 30 seconds default (configurable via `AI_TIMEOUT`)

### Test Categories

- **Unit tests**: Fast tests without external dependencies
- **Integration tests**: Tests that call real APIs (marked with `@pytest.mark.integration`)

Integration tests are automatically skipped if API keys are missing. Other skipped test categories include:
- **Live provider tests**: Require `RUN_LIVE_AI_TESTS=1` environment variable
- **File integration tests**: Require `--run-integration` flag and test files
- **Audio integration tests**: Require API keys and audio files
- **Slow tests**: Require `--run-slow` flag (performance/settings tests)

### Live Integration Tests

For comprehensive testing with real API calls, run live integration tests:

```bash
export RUN_LIVE_AI_TESTS=1 && python -m pytest -m integration --run-integration -v --timeout=120
```

**Requirements:**
- `RUN_LIVE_AI_TESTS=1` environment variable must be set
- Provider API keys configured in environment or `.env` file
- Local provider servers running (if testing local providers)

**Note:** Provider-specific tests may skip if their respective API keys or servers are not configured.

### Coverage Testing

This repository uses tox for consistent coverage testing and reporting.

#### Coverage Commands

**Run tests with coverage:**
```bash
tox -e coverage
```

**Coverage Reports:**
- Terminal report: Displayed during run
- XML report: `coverage_reports/coverage.xml` (for CI tools)
- HTML report: `coverage_reports/html/` (detailed browser view)

**Run specific tests with coverage:**
```bash
tox -e coverage -- tests/test_specific_file.py
```

**Important Notes:**
- Coverage reports are automatically generated in `coverage_reports/`
- XML report at `coverage_reports/coverage.xml` for CI integration
- HTML report at `coverage_reports/html/` for detailed viewing

### Packaging Smoke Tests

Packaging smoke tests validate that the wheel can be installed and imported correctly in clean environments. These tests are critical for ensuring distribution quality.

**How to run:**
```bash
# Run packaging smoke tests
RUN_PACKAGING_TESTS=1 python -m pytest tests/packaging -v

# Or use tox
tox -e packaging
```

**What each test guarantees:**

1. **Strict no-deps import** (`test_wheel_install_no_deps_import_smoke`)
   - Wheel can be installed with `--no-deps` (no dependencies)
   - `import ai_utilities` works without any external dependencies
   - Validates that optional dependencies remain truly optional

2. **Realistic install + CLI help** (`test_wheel_install_with_deps_cli_help_and_import`)
   - Wheel can be installed normally (with dependencies resolved)
   - `import ai_utilities` works with all runtime dependencies
   - `ai-utilities --help` works (validates entry point from [project.scripts])

3. **OpenAI extra + provider import** (`test_wheel_install_openai_extra_cli_help_and_openai_provider_import`)
   - Package can be installed with the OpenAI extra dependency
   - OpenAI provider module can be imported (offline validation)
   - CLI help continues to work with optional dependencies

**Key Features:**
- **Environment isolation**: Each test runs in a clean virtual environment
- **No network calls**: Tests validate offline import behavior only
- **Gated execution**: Tests only run when `RUN_PACKAGING_TESTS=1` is set
- **Comprehensive validation**: Covers wheel building, installation, import, and CLI functionality

### Project Structure Protection

This repository includes automated tests to prevent project structure pollution and maintain clean organization.

**Protected Structure Rules:**
- **Coverage reports**: Only in `coverage_reports/` at repository root
- **No coverage files**: In `tests/` directory or subdirectories  
- **No duplicate directories**: `htmlcov/`, `reports/` in wrong locations
- **Test artifacts**: Only in appropriate locations (never in root except `.pytest_cache`)

**Automated Enforcement:**
```bash
# Run structure validation tests
python -m pytest tests/test_project_structure.py -v
```

**Directory Standards:**
```
ai_utilities/
├── coverage_reports/          # ✅ Only coverage reports location
│   ├── .coverage              # Coverage data file
│   ├── html/                  # HTML reports
│   └── .gitignore             # Excludes all files except itself
├── reports/                   # ✅ Manual reports and test outputs
│   ├── manual_report_*.md     # Generated reports
│   └── test_output/           # Test artifacts
├── tests/                     # ✅ Test files only (no coverage data)
│   └── test_*.py
└── .pytest_cache              # ✅ Allowed standard pytest artifact
```

This prevents the common problem of coverage reports and test artifacts being scattered throughout the project, maintaining a clean and predictable structure.

### Test Hygiene

**Tests must not write to repository root.** All test artifacts must be created in temporary directories.

- **Use `tmp_path` fixture**: For per-test temporary files
- **Use `tmp_path_factory`**: For session-scoped temporary directories  
- **Never write to root**: Tests will fail if they create files in repository root
- **Guardrail enforcement**: Automatic detection prevents root artifact creation

#### Example
```python
def test_with_temp_files(tmp_path):
    # Good: Use tmp_path for test files
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
    
    # Bad: Don't write to repository root
    # Path("root_file.txt").write_text("content")  # Will fail!
```

#### Convenience Commands (Makefile)

```bash
make test      # Run full test suite with coverage
make test-fast # Run tests quietly  
make cov       # Run tests with coverage reports (term + html)
make help      # Show all available targets
```

#### Handling Long Output

```bash
# Pipe coverage output to file and view last 100 lines
python -m pytest --cov-report=term-missing > /tmp/cov.txt && tail -100 /tmp/cov.txt
```

⚠️ **Anti-footgun**: If you run `python -m coverage run -m pytest`, you'll see pytest-cov reports during the run, but `coverage report` afterwards will show 0% because the outer coverage session collected nothing.

For detailed testing guidelines, see [CI_TIMEOUT_GUIDELINES.md](CI_TIMEOUT_GUIDELINES.md) and [Testing Setup Guide](docs/testing-setup.md).

## Troubleshooting: urllib3 LibreSSL warning (macOS)

When running tests or using the library on macOS, you may see this warning:

```
urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
```

### Why this happens
- urllib3 v2 requires OpenSSL 1.1.1+ for optimal HTTPS operations
- Apple Command Line Tools Python can be linked with LibreSSL instead of OpenSSL
- This mismatch triggers a `NotOpenSSLWarning` but doesn't break functionality

### Check your SSL backend
```bash
python -c "import ssl; print(ssl.OPENSSL_VERSION)"
```

If it shows "LibreSSL", you're using Apple's Python build.

### How to resolve
Use a Python build linked against OpenSSL:

**Option 1: python.org installer**
```bash
# Download from python.org and reinstall your venv
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Option 2: Homebrew**
```bash
brew install python@3.11
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Option 3: pyenv**
```bash
pyenv install 3.11.7
pyenv local 3.11.7
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Note for contributors
- The warning is safe to ignore for development and testing
- CI/Linux environments typically use OpenSSL, so you may not see it there
- Only HTTPS-heavy production workloads need the OpenSSL-linked Python for optimal performance

## Testing & Stability

This project is heavily tested by design.

The test suite includes:
- Extensive unit tests across all public APIs
- Contract tests to prevent undocumented breaking changes
- Coverage enforcement and CI validation across multiple Python versions
- Regression tests for previously fixed edge cases

The goal is simple:
changes should be safe, refactors should be boring, and examples in the
documentation should continue to work over time.

If something breaks, it is considered a bug — not expected behavior.

## Pre-release staging on PyPI

### Automatic Pre-release Publishing

Pre-release tags (containing `a`, `b`, or `rc`) are automatically published to real PyPI as pre-releases:

```bash
git tag v1.0.1b1
git push origin v1.0.1b1
```

The workflow includes an automatic smoke test that installs the published package from PyPI and verifies it works correctly.

### Manual Pre-release Publishing

You can manually trigger a pre-release publish in GitHub Actions:
1. Go to Actions tab in GitHub
2. Select "Publish Pre-release to PyPI" workflow
3. Click "Run workflow"

### Installing Pre-releases

Test pre-release versions before they're published as stable releases:

```bash
pip install --pre ai-utilities
python -c "import ai_utilities; print(ai_utilities.__version__)"
ai-utilities --help
```

Or install a specific pre-release version:

```bash
pip install ai-utilities==1.0.1b1 --pre
```

### Production Publishing

Stable release tags (e.g., `v1.0.0`) are published to PyPI via the main `publish.yml` workflow.

**Note:** TestPyPI is not usable for this project name due to similarity restrictions, so we use real PyPI pre-releases for staging.

## Where to Go Next

### User Documentation
- [Getting Started Guide](docs/user/getting-started.md) - Detailed setup and examples
- [Configuration Guide](docs/user/configuration.md) - All environment variables
- [Provider Setup](docs/user/providers.md) - Provider-specific configuration
- [Smart Caching](docs/user/caching.md) - Reduce API costs with caching
- [Troubleshooting Guide](docs/user/troubleshooting.md) - Common issues and solutions

### Releasing

#### Stable Releases
1. Update version in `pyproject.toml` to stable version (e.g., `1.0.0`)
2. Run Actions workflow "Create Release Tag" which:
   - Reads version from `pyproject.toml`
   - Validates version is stable (no pre-release identifiers)
   - Runs unit tests
   - Creates and pushes tag `v<version>`
3. Tag triggers "Publish to PyPI" workflow automatically

#### Pre-releases
1. Update version in `pyproject.toml` to pre-release version (e.g., `1.0.0b1`, `1.0.0a1`, `1.0.0rc1`)
2. Push tag `v<version>` to trigger "Publish Pre-release to PyPI"
   - OR run "Publish Pre-release to PyPI" workflow manually

**Important**: Tags must match `pyproject.toml` version exactly. Workflows enforce this consistency and will fail if tag version differs from project version.

### Development
- For development setup see [CONTRIBUTING.md](CONTRIBUTING.md)
- [Development Documentation](docs/dev/development-setup.md)
- [Architecture Overview](docs/dev/architecture.md)
- [Testing Guide](docs/testing-guide.md)

For development setup and contributing, see CONTRIBUTING.md

---

MIT License - see [LICENSE](LICENSE) file for details.
