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

#### Unit Tests (Fast)
```bash
# Run unit tests only (no external API calls)
pytest -m "not integration" --timeout=30
```

#### Integration Tests (Requires API Keys)

Integration tests automatically load environment variables from the `.env` file, so you only need to set up the `.env` file:

```bash
# Option 1: Use .env file (recommended)
# Create .env file with your API key
echo "AI_API_KEY=your-api-key" >> .env

# Run integration tests (will automatically use .env)
pytest -m "integration" --timeout=120

# Option 2: Export manually (alternative to .env)
export AI_API_KEY=your-api-key
pytest -m "integration" --timeout=120
```

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

### Coverage Testing

This repository uses coverage.py for accurate test coverage measurement. Use the following commands for consistent coverage results.

#### Coverage Commands

**Run tests with coverage:**
```bash
COVERAGE_FILE=coverage_reports/.coverage coverage run -m pytest -q
```

**Generate HTML report:**
```bash
coverage html -d coverage_reports/html
```

**Show terminal coverage report:**
```bash
coverage report -m
```

**Run specific test file with coverage:**
```bash
COVERAGE_FILE=coverage_reports/.coverage coverage run -m pytest tests/test_specific_file.py -q
```

**Coverage for specific module:**
```bash
COVERAGE_FILE=coverage_reports/.coverage coverage run -m pytest tests/test_specific_file.py -q --cov=ai_utilities.module_name --cov-report=term-missing
```

**Important Notes:**
- Always use `COVERAGE_FILE=coverage_reports/.coverage` to ensure coverage data is stored in the correct location
- The `-m` flag shows missing lines in the coverage report
- HTML reports are generated in `coverage_reports/html/` for detailed viewing
- Coverage data accumulates - use `coverage erase` to reset if needed

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
- [Troubleshooting Guide](docs/user/troubleshooting.md) - Common issues and solutions

### Development
- For development setup see [CONTRIBUTING.md](CONTRIBUTING.md)
- [Development Documentation](docs/dev/development-setup.md)
- [Architecture Overview](docs/dev/architecture.md)
- [Testing Guide](docs/dev/testing.md)

For development setup and contributing, see CONTRIBUTING.md

---

MIT License - see [LICENSE](LICENSE) file for details.
