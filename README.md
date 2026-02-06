# AI Utilities

A Python library for AI model interaction with unified interface, intelligent caching, and type safety. Use OpenAI, Groq, Together AI, Ollama, and other providers with the same code.

## Who This Is For

AI Utilities is for developers who need to integrate AI capabilities into their applications without being locked into a single provider. It's designed for both beginners who want simple AI interactions and advanced users who need production-ready features like caching and rate limiting.

## What Problem It Solves

Managing multiple AI providers is complex and error-prone. Each provider has different APIs, authentication methods, and error handling. AI Utilities solves this by providing a single, consistent interface that works across all major providers while adding enterprise features like intelligent caching and comprehensive error handling.

## Quickstart

### Install

```bash
pip install ai-utilities[openai]
```

### Basic Usage

```python
from ai_utilities import AiClient

# Create client (loads from .env file automatically)
client = AiClient()

# Make a request
response = client.ask("What is the capital of France?")
print(response)

# Monitor usage (if tracking enabled)
usage_stats = client.get_usage_stats()
if usage_stats:
    print(f"Tokens used: {usage_stats.total_tokens}")
```

### Configuration

Create a `.env` file:

```bash
# Option 1: Auto-select among configured providers (recommended)
AI_PROVIDER=auto

# Option 2: Use specific provider
# AI_PROVIDER=openai

# Configure one or more providers below
# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4

# Groq (fast inference)
# GROQ_API_KEY=your-groq-key
# GROQ_MODEL=llama3-70b-8192

# Together AI (open source models)
# TOGETHER_API_KEY=your-together-key
# TOGETHER_MODEL=mistral-7b

# OpenRouter (multiple model access)
# OPENROUTER_API_KEY=your-openrouter-key
# OPENROUTER_MODEL=anthropic/claude-3-haiku

# Local providers (require model)
# OLLAMA_BASE_URL=http://localhost:11434/v1
# OLLAMA_MODEL=llama3.1

# FastChat
# FASTCHAT_BASE_URL=http://localhost:8000/v1
# FASTCHAT_MODEL=your-model-name

# Text Generation WebUI
# TEXT_GENERATION_WEBUI_BASE_URL=http://localhost:5000/v1
# TEXT_GENERATION_WEBUI_MODEL=your-model-name

# OpenAI Compatible (custom endpoints)
# AI_BASE_URL=https://your-endpoint.com/v1
# AI_API_KEY=your-key
# AI_MODEL=your-model

# Optional: Override auto-selection order
# AI_AUTO_SELECT_ORDER=openai,groq,openrouter,together,ollama,fastchat,text-generation-webui
```

Or run the interactive setup:

```bash
ai-utilities setup
```

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

- **OpenAI** - GPT-4, GPT-3.5-turbo, audio processing
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
   # OpenAI: gpt-4, gpt-3.5-turbo
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

## Where to Go Next

### User Documentation
- [Getting Started Guide](docs/user/getting-started.md) - Detailed setup and examples
- [Configuration Guide](docs/user/configuration.md) - All environment variables
- [Provider Setup](docs/user/providers.md) - Provider-specific configuration
- [Smart Caching](docs/user/caching.md) - Reduce API costs with caching
- [Metrics and Monitoring](docs/user/metrics.md) - Track performance and usage
- [Troubleshooting Guide](docs/user/troubleshooting.md) - Common issues and solutions

### Development
- For development setup see [CONTRIBUTING.md](CONTRIBUTING.md)
- [Development Documentation](docs/dev/development-setup.md)
- [Architecture Overview](docs/dev/architecture.md)
- [Testing Guide](docs/dev/testing.md)

For development setup and contributing, see CONTRIBUTING.md

---

MIT License - see [LICENSE](LICENSE) file for details.
