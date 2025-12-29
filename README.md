# AI Utilities v1

A Python library for AI model interaction with **Pydantic configuration**, **Single Responsibility Principle architecture**, and **dynamic rate limit management**.

## ⚡ 20-Second Quickstart

```bash
# Install
pip install ai-utilities

# Option 1: Create .env file (recommended for local dev)
echo "AI_API_KEY=your-openai-key" > .env

# Option 2: Set environment variable
export AI_API_KEY="your-openai-key"

# Use in Python
python -c "
from ai_utilities import AiClient
client = AiClient()
print(client.ask('What is AI?'))
"
```

**Where to look next:**
- **More examples** → [`examples/`](examples/)
- **Configuration reference** → [Configuration](#configuration)
- **API reference** → Use `help(AiClient)` in Python
- **Changelog / versions** → [GitHub Releases](https://github.com/audkus/ai_utilities/releases)

---

## 📁 Project Structure

```
ai_utilities/
├── 📄 README.md              # Main documentation
├── 📄 pyproject.toml         # Package configuration  
├── 📄 main.py                # Entry point
├── 📄 .env                   # Environment variables
├── 📁 src/                   # Core library code
│   └── 📁 ai_utilities/      # Main package
├── 📁 tests/                 # Test suite
│   ├── 📁 provider_monitoring/ # Provider monitoring tests
│   ├── 📁 integration/        # Integration tests
│   ├── 📁 demo/              # Demo app tests
│   └── 📋 [20+ test files]   # Core library tests
├── 📁 scripts/               # Utility & monitoring tools
│   ├── 🏥 provider_health_monitor.py      # Core monitoring system
│   ├── 🔍 provider_change_detector.py     # Change detection
│   ├── 🌅 daily_provider_check.py         # Daily health check
│   └── 🚀 ci_provider_check.sh            # CI/CD script
├── 📁 examples/              # Usage examples
├── 📁 .github/               # CI/CD workflows
│   └── 📁 workflows/         # GitHub Actions
└── 📁 docs/                  # Additional documentation
```

### 🎯 Key Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **`src/`** | Core library code | Main AI utilities package |
| **`tests/`** | Test suite | Unit tests, integration tests, provider monitoring |
| **`scripts/`** | Utility tools | Health monitoring, change detection, CI/CD |
| **`examples/`** | Usage examples | Code samples and demos |
| **`.github/`** | CI/CD | Automated workflows and monitoring |

---

## 🔑 API Key Setup

Choose **one** of these methods to configure your OpenAI API key:

### 1️⃣ .env File (Recommended for Local Development)

Create a `.env` file in your project directory:

```bash
# Create .env file
echo "AI_API_KEY=your-openai-key-here" > .env
```

**Works in:** Terminal, PyCharm, VS Code, any IDE  
**Best for:** Local development, team projects

### 2️⃣ Environment Variable (Current Session)

```bash
# macOS/Linux
export AI_API_KEY="your-openai-key-here"

# Windows PowerShell
$env:AI_API_KEY="your-openai-key-here"

# Windows Command Prompt
set AI_API_KEY=your-openai-key-here
```

**Works in:** Current terminal session only  
**Best for:** Quick tests, CI/CD, one-off usage

### 3️⃣ PyCharm IDE Configuration

1. **Run/Debug Configurations** → **Environment variables**
2. Click **+** to add: `AI_API_KEY=your-openai-key-here`
3. Apply and run

**Works in:** PyCharm only  
**Best for:** PyCharm development without terminal setup

### 4️⃣ Direct Override (Tests/One-off)

```python
from ai_utilities import create_client

# Pass API key directly
client = create_client(api_key="your-openai-key-here")
```

**Works in:** Any Python code  
**Best for:** Tests, scripts, temporary usage

---

## 🔑 API Key Usage Guide

### ⚠️ Important Note for Some Providers

While most providers work with environment variables, **some cloud providers require explicit API key passing** for reliable operation:

```python
from ai_utilities import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# ✅ RECOMMENDED: Use explicit api_key for consistency
client = create_client(
    provider="openai_compatible",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),  # Explicit key
    model="llama-3.1-8b-instant"
)

# ✅ This pattern works consistently for ALL providers
providers = [
    {
        "name": "Groq",
        "config": {
            "provider": "openai_compatible",
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": os.getenv("GROQ_API_KEY"),
            "model": "llama-3.1-8b-instant"
        }
    },
    {
        "name": "Together AI",
        "config": {
            "provider": "openai_compatible", 
            "base_url": "https://api.together.xyz/v1",
            "api_key": os.getenv("TOGETHER_API_KEY"),
            "model": "meta-llama/Llama-3.2-3B-Instruct-Turbo"
        }
    },
    {
        "name": "OpenRouter",
        "config": {
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1", 
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model": "meta-llama/llama-3.2-3b-instruct:free"
        }
    }
]

# Use the same pattern for all providers
for provider in providers:
    client = create_client(**provider["config"])
    response = client.ask("Hello!", max_tokens=10)
    print(f"{provider['name']}: {response}")
```

### 📋 Provider Status

| Provider | Environment Variables | Explicit Key | Recommendation |
|----------|---------------------|--------------|----------------|
| **OpenAI** | ✅ Works | ✅ Works | Use either method |
| **Groq** | ❌ May fail | ✅ Works | **Use explicit key** |
| **Together AI** | ❌ May fail | ✅ Works | **Use explicit key** |
| **OpenRouter** | ❌ May fail | ✅ Works | **Use explicit key** |
| **Ollama** | ✅ Works | ✅ Works | Use either method |
| **LM Studio** | ✅ Works | ✅ Works | Use either method |

### 💡 Best Practice

**For maximum compatibility across all providers, always use explicit `api_key` parameter:**

```python
# ✅ Universal pattern - works for every provider
from ai_utilities import create_client
import os

client = create_client(
    provider="openai_compatible",
    base_url="your-provider-url",
    api_key=os.getenv("YOUR_API_KEY"),  # Always explicit
    model="your-model"
)
```

This ensures your code works consistently regardless of which AI provider you use!

---

## Configuration

### Environment Variables (Recommended)

Set these in your environment or `.env` file:

```bash
# Required for OpenAI
export AI_API_KEY="your-openai-key"

# Additional provider API keys (for explicit key usage)
export GROQ_API_KEY="your-groq-key"
export TOGETHER_API_KEY="your-together-key"
export OPENROUTER_API_KEY="your-openrouter-key"

# Optional
export AI_MODEL="gpt-4"
export AI_TEMPERATURE="0.7"
export AI_MAX_TOKENS="1000"
export AI_TIMEOUT="30"
```

### Explicit Settings

```python
from ai_utilities import AiClient, AiSettings

# Create settings explicitly
settings = AiSettings(
    api_key="your-key",
    model="gpt-4",
    temperature=0.5
)

# Use with client
client = AiClient(settings)
response = client.ask("What is the capital of France?")
```

---

### 🚀 Key Features:
- **🔧 Pydantic Settings Configuration**: Type-safe, validated configuration with environment variable integration and SettingsConfigDict
- **🏗️ Provider Architecture**: Clean provider pattern with BaseProvider abstraction and OpenAIProvider implementation
- **📊 Dynamic Rate Limit Fetching**: Automatic OpenAI rate limit detection with 30-day caching to conserve API credits
- **🔒 Thread-Safe Usage Tracking**: Concurrent usage tracking with configurable scoping (per-client, per-process, global)
- **⚡ Parallel AI Calls**: Multi-threaded AI requests with race condition prevention and accurate statistics
- **🔄 Sync & Async Clients**: Both synchronous and asynchronous AI client interfaces
- **🌍 Environment Precedence System**: Settings with clear precedence: init kwargs > override_env > os.environ > defaults
- **🤖 Simple AI Interaction**: Use `AiClient.ask()` or `AsyncAiClient.ask()` for single or multiple prompts
- **🔍 Smart Setup**: Automatic detection of missing API keys and new OpenAI models (configurable interval)
- **🔌 Provider Abstraction**: Clean provider pattern supporting OpenAI with extensible architecture
- **⏱️ Progress Indicators**: Built-in progress display showing request duration (configurable)
- **📈 Usage Tracking**: Optional token and request tracking with persistent statistics
- **📦 Batch Processing**: Efficient handling of multiple prompts with concurrency control
- **📄 JSON Mode**: Native JSON response support with fallback extraction
- **🛡️ No Import-Time Side Effects**: Clean architecture with explicit configuration
- **🔧 Environment Override Context**: Thread-safe contextvar-based environment overrides with `override_env`

---

## External Libraries and Models

The `ai_utilities` project integrates with external libraries to provide AI interaction and configuration management.

### 1. OpenAI Models

We use OpenAI's models for generating responses to user prompts. The models are accessed via OpenAI's official Python SDK, and you can select which model to use through environment variables or explicit settings.

#### Models Supported:

The library is designed to work with **any OpenAI model** and does not hardcode model availability. Instead, it:

- ✅ **Validates models dynamically** against the OpenAI API
- ✅ **Adapts to new models** automatically via smart setup
- ✅ **Uses flexible model detection** for features like JSON mode
- ✅ **Provides graceful fallbacks** when model validation fails

**Current popular models** (examples only):
- `gpt-4` series (including turbo variants)
- `gpt-3.5-turbo` series  
- `gpt-4o` series
- Custom fine-tuned models

**Note:** Model names in examples are for illustration only. The library works with any model available in your OpenAI account.

#### Configuration:
```bash
# Environment variables
export AI_API_KEY="your-openai-key"
export AI_MODEL="gpt-4"
export AI_TEMPERATURE="0.7"
```

### 2. Core Dependencies

- **openai** (>=1.0,<3): Official OpenAI Python SDK
- **pydantic** (>=2.0): **Type-safe configuration validation** with immutability and environment variable integration
- **pydantic-settings**: Environment-based configuration management
- **portalocker** (>=2.0,<3): **Cross-platform file locking** for thread-safe usage tracking and concurrent access
- **datetime**: Built-in Python library for time-based caching (model update checks and rate limit caching)

#### 🏗️ Architecture Components

The library follows a **clean provider architecture** with specialized components:

- **AiClient**: Main client interface with provider abstraction
- **AsyncAiClient**: Asynchronous client interface
- **AiSettings**: Pydantic-based configuration with SettingsConfigDict
- **BaseProvider**: Abstract provider interface for extensibility
- **OpenAIProvider**: OpenAI-specific provider implementation
- **UsageTracker**: Thread-safe usage tracking with configurable scoping
- **ProgressIndicator**: Built-in progress display for requests
- **RateLimitFetcher**: Dynamic rate limit detection with 30-day caching
- **TokenCounter**: Multi-method token counting algorithms
- **override_env**: Thread-safe contextvar-based environment overrides

#### Setup and API Key

**For Development/Testing:**

**Option 1: Interactive Setup (Recommended for New Users)**

The easiest way to get started is using the interactive setup, which automatically detects missing configuration and guides you through secure setup options:

```python
from ai_utilities import AiClient

# Automatically prompts for setup if API key is missing
client = AiClient()  # Interactive setup will start if needed
response = client.ask("What is the capital of France?")
```

**Option 2: Smart Setup (Automatic Model Updates)**

Smart setup includes interactive setup plus automatic checking for new OpenAI models:

```python
from ai_utilities import AiClient, AiSettings

# Smart setup (checks for new models every 30 days by default)
client = AiClient(smart_setup=True)
response = client.ask("What is the capital of France?")

# Custom check interval (e.g., check every 7 days)
settings = AiSettings(update_check_days=7)
client = AiClient(settings=settings, smart_setup=True)
```

**Security Options in Interactive Setup:**
- 🔒 **Environment Variable Method** (Recommended): Set `AI_API_KEY` and restart
  - Shows only commands for your OS (Windows PowerShell/CMD or Linux/Mac)
  - Clear instructions to use only the command matching your terminal
- ⚠️ **Direct Input** (Less Secure): Type key directly (visible in terminal history)
- 📁 **.env File**: Save to local file (ensure it's git-ignored)

**Smart Setup Features:**
- ✅ **Auto-detection**: Automatically detects missing API keys
- ✅ **Security-focused**: Multiple secure input options with warnings
- ✅ **Model Updates**: Checks for new OpenAI models (configurable interval)
- ✅ **Cost-aware**: Caches results to minimize API calls and token usage
- ✅ **Detailed Display**: Shows new models and current models when updates found
- ✅ **Configurable Interval**: Default 30 days, adjustable per needs
- ✅ **Manual Control**: Force checks or reconfigure anytime

**Option 3: Manual Environment Variables**

To use OpenAI's models during development, you can manually set environment variables:

1. Sign up at [OpenAI's website](https://platform.openai.com/) and obtain an API key.
2. Set the API key as an environment variable on your system:
   - **For Linux/Mac**:
     ```bash
     export AI_API_KEY='your-api-key-here'
     ```
   - **For Windows**:
     ```powershell
     $env:AI_API_KEY='your-api-key-here'
     ```

3. Optionally, configure additional settings:
   ```bash
   export AI_MODEL="gpt-4"
   export AI_TEMPERATURE="0.7"
   export AI_MAX_TOKENS="1000"
   export AI_UPDATE_CHECK_DAYS="30"  # Model update check interval
   ```

**Option 4: Force Reconfiguration**

If you want to change your existing configuration:

```python
from ai_utilities import AiSettings

# Force reconfiguration prompt
settings = AiSettings.reconfigure()
client = AiClient(settings)
```

**For Application Deployment:**

When building applications that use ai_utilities, you have several options:

**Option 1: Environment Variables (Recommended for Production)**
```python
# Application code - no hardcoded credentials
from ai_utilities import AiClient

client = AiClient()  # Automatically reads from environment
response = client.ask("Your question")
```

Set environment variables in your deployment environment:
```bash
# Docker/Container
ENV AI_API_KEY="your-production-key"
ENV AI_MODEL="gpt-3.5-turbo"

# Kubernetes/Cloud
# Configure via secrets or environment variable management

# Systemd/Service
Environment=AI_API_KEY="your-production-key"
```

**Option 2: Explicit Configuration (For Multi-tenant Apps)**
```python
from ai_utilities import AiClient, AiSettings

# Load from your app's configuration system
app_settings = load_app_config()  # Your config loading

ai_settings = AiSettings(
    api_key=app_settings.openai_key,
    model=app_settings.ai_model,
    temperature=app_settings.ai_temperature
)

client = AiClient(ai_settings)
```

**Option 3: Configuration File (For Legacy Support)**
```python
from ai_utilities import AiSettings

# Explicit file loading (not automatic)
settings = AiSettings.from_ini("/path/to/config.ini")
client = AiClient(settings)
```

**Security Best Practices:**
- Never hardcode API keys in source code
- Use environment variables or secret management in production
- Rotate API keys regularly
- Use different keys for development and production
- Consider using OpenAI's project-based API keys for better access control

**N.B.** You probably need to restart your IDE for this to take effect.

#### Licensing and Usage Limits

- OpenAI's GPT models are licensed under OpenAI's [terms of service](https://openai.com/terms).
- The API has rate limits that are automatically handled by OpenAI's infrastructure.
- OpenAI charges for API usage, and you should review their [pricing](https://openai.com/pricing) to understand the costs involved.
- Optional usage tracking is available to monitor your API consumption.

---

## Installation

### From Source

```bash
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### For Developers (Editable Install)

If you're developing the library or need to make changes, install it in editable mode from the repository root (where `pyproject.toml` is located):

```bash
# From the repository root
python -m pip install -e .

# Verify installation works
python -c "from ai_utilities import AiClient, create_client; print('OK')"
```

**Why editable install for developers:**
- Changes to source code are immediately reflected without reinstalling
- Allows you to test your modifications directly
- Required for running tests and development tools

### Dependencies

The project automatically installs all required dependencies:

- **openai** (>=1.0,<3): Official OpenAI Python SDK
- **pydantic** (>=2.0): Data validation and settings management
- **pydantic-settings**: Environment-based configuration

### Optional Dependencies

For development and testing:

```bash
pip install -e ".[dev]"
```

**Development tools included:**
- **pytest** (>=8,<9): Test framework for running unit and integration tests
- **pytest-cov** (>=5,<7): Test coverage reporting
- **pytest-asyncio** (>=0.21,<1): Async test support for pytest
- **ruff** (>=0.6,<1): Fast Python linter and formatter with import checking
- **mypy** (>=1.10,<2): Static type checking
- **types-setuptools**: Type stubs for setuptools

**Type Safety:**
- Includes `py.typed` marker file for PEP 561 compliance
- Full type annotations on public APIs
- mypy-compatible for downstream users

**Version Management:**
- Automatic version detection using `importlib.metadata`
- Single source of truth in `pyproject.toml`
- No more version mismatches between package and code

**Usage examples:**
```bash
# Code quality (run before committing)
ruff check .          # Check for linting issues
ruff check . --fix    # Auto-fix linting issues
ruff format .         # Format code

# Testing
pytest                # Run tests
pytest --cov=ai_utilities  # Tests with coverage
pytest -v             # Verbose test output
pytest -m "not slow"  # Skip slow tests

# Type checking
mypy src/             # Type check the source code
```

### Testing Framework

This project uses **pytest** as the testing framework (not unittest):

**Test Structure:**
- Test files follow pytest convention: `test_*.py`
- Test functions use pytest naming: `test_*()`
- Uses pytest fixtures with `@pytest.fixture`
- Async tests use `@pytest.mark.asyncio`
- Custom markers available: `@pytest.mark.slow`

**Key Differences from unittest:**
```python
# pytest style (used in this project)
def test_function():
    with pytest.raises(ValueError):
        # test code
    assert result == expected

# unittest style (NOT used)
class TestClass(unittest.TestCase):
    def test_method(self):
        with self.assertRaises(ValueError):
            # test code
        self.assertEqual(result, expected)
```

**Running Tests:**
```bash
# Run all tests (includes automatic Ruff import checking)
pytest

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest -v

# Skip slow tests
pytest -m "not slow"

# Run only slow tests
pytest -m slow
```

### Import Checking with Ruff

This project uses **Ruff** for comprehensive code quality checking including import validation:

**Features:**
- **Import validation**: Detects unused imports, missing imports, and import order issues
- **Auto-fix capability**: Automatically fixes import issues and code style problems
- **Fast performance**: Written in Rust for lightning-fast linting
- **Comprehensive rules**: Includes import errors, unused imports, code style, and more

**Ruff Configuration:**
- Enabled rules: Import errors, unused imports, import sorting, code quality
- Auto-fix enabled for all fixable issues
- Configured for `src/` layout with proper first-party detection
- Line length: 88 characters (Black compatible)

**Usage:**
```bash
# Check for issues (including import problems)
ruff check .

# Auto-fix issues (including import cleanup)
ruff check . --fix

# Format code (including import sorting)
ruff format .

# Check specific file
ruff check src/ai_utilities/client.py

# Run both check and format
ruff check . --fix && ruff format .
```

**Recommended Workflow:**
```bash
# Before committing changes
ruff check . --fix    # Fix linting issues
ruff format .         # Format code
pytest                # Run tests
```

---

## 📚 Documentation

- **📖 [Main README](README.md)** - Project overview and quick start
- **📋 [Documentation](docs/)** - Detailed guides and documentation
  - [Testing Setup](docs/testing-setup.md) - Complete testing guide
  - [All Providers Guide](docs/all-providers-guide.md) - Comprehensive provider documentation
  - [Ollama Capabilities](docs/ollama-capabilities.md) - Ollama-specific guide

## 🚀 Quick Start

### 1. Set Up Environment

```bash
# Set your OpenAI API key
export AI_API_KEY="your-openai-key"

# Optional: Configure default model and settings
export AI_MODEL="gpt-4"
export AI_TEMPERATURE="0.7"
```

### 2. Basic Usage

```python
from ai_utilities import AiClient

# Create client (automatically uses environment variables or prompts for setup)
client = AiClient()

# Ask a single question
response = client.ask("What is the capital of France?")
print(response)

# Ask multiple questions
questions = ["What is 2+2?", "What is the capital of Spain?"]
responses = client.ask_many(questions)
for question, answer in zip(questions, responses):
    print(f"Q: {question}")
    print(f"A: {answer}")
```

**Import Notes:**
- ✅ **Works when installed**: `from ai_utilities import AiClient` works after `pip install ai-utilities`
- ✅ **Works in development**: Examples automatically add `src` to Python path for repo usage  
- ✅ **Consistent interface**: Same import pattern whether developing or using installed package

### 3. 🌐 Provider Configuration

The library supports multiple AI providers while maintaining the same `AiClient.ask()` API. Switch between OpenAI (cloud) and local OpenAI-compatible servers via configuration.

#### OpenAI Provider (Default)

```python
from ai_utilities import AiClient, AiSettings

# Using environment variables (default)
export AI_API_KEY="your-openai-key"
export AI_PROVIDER="openai"  # This is the default

client = AiClient()
response = client.ask("What is AI?")
```

#### Local OpenAI-Compatible Provider

```python
from ai_utilities import AiClient, AiSettings

# Method 1: Environment variables
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:11434/v1"  # Ollama
export AI_API_KEY="dummy-key"  # Optional for local servers

client = AiClient()
response = client.ask("What is AI?")

# Method 2: Explicit settings
settings = AiSettings(
    provider="openai_compatible",
    base_url="http://localhost:8000/v1",  # vLLM or other local server
    api_key="dummy-key",  # Optional for local servers
    model="llama2-7b",
    temperature=0.8
)

client = AiClient(settings)
response = client.ask("Explain quantum computing")
```

#### Popular Local Server Examples

```bash
# Ollama (http://localhost:11434/v1)
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:11434/v1"
export AI_MODEL="llama2"

# vLLM (http://localhost:8000/v1)
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:8000/v1"
export AI_MODEL="vicuna-13b-v1.5"

# LM Studio (http://localhost:1234/v1)
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:1234/v1"
export AI_MODEL="local-model"
```

#### Advanced Provider Configuration

```python
from ai_utilities import AiSettings

# Custom headers for gateways or authentication
settings = AiSettings(
    provider="openai_compatible",
    base_url="https://api.example.com/v1",
    api_key="your-api-key",
    extra_headers={
        "Authorization": "Bearer custom-token",
        "X-Model-Provider": "custom-gateway"
    },
    request_timeout_s=60.0,  # Float timeout
    model="custom-model"
)

client = AiClient(settings)
```

**Provider Features:**
- ✅ **OpenAI**: Full feature support (JSON mode, tools, streaming, images)
- ⚠️ **OpenAI-Compatible**: Text responses + basic parameters (JSON mode varies by server)
- 🔄 **Same API**: `client.ask()` works identically across all providers
- 🛡️ **Error Handling**: Clear errors for missing configuration or unsupported features

### 4. 🔄 Sync & Async Client Examples

#### Synchronous Client (AiClient)

```python
from ai_utilities import AiClient, AskResult

# Create synchronous client
client = AiClient()

# Single request
response = client.ask("What is the capital of France?")
print(response)

# Multiple requests (sequential execution)
prompts = [
    "What is the capital of France?",
    "What is the capital of Germany?", 
    "What is the capital of Spain?"
]

results = client.ask_many(prompts)
for result in results:
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Response: {result.response}")
        print(f"Duration: {result.duration_s:.2f}s")
```

#### Asynchronous Client (AsyncAiClient)

```python
import asyncio
from ai_utilities import AsyncAiClient, AskResult

async def main():
    # Create asynchronous client
    client = AsyncAiClient()
    
    # Single request
    response = await client.ask("What is the capital of France?")
    print(response)
    
    # Multiple requests (parallel execution with concurrency control)
    prompts = [
        "What is the capital of France?",
        "What is the capital of Germany?", 
        "What is the capital of Spain?",
        "What is the capital of Italy?",
        "What is the capital of Portugal?"
    ]
    
    def progress_callback(completed: int, total: int):
        print(f"Progress: {completed}/{total}")
    
    results = await client.ask_many(
        prompts, 
        concurrency=3,  # Max 3 concurrent requests
        on_progress=progress_callback
    )
    
    for result in results:
        if result.error:
            print(f"Error: {result.error}")
        else:
            print(f"Response: {result.response}")
            print(f"Duration: {result.duration_s:.2f}s")

# Run async main
asyncio.run(main())
```

#### Mixing Sync + Async

```python
import asyncio
from ai_utilities import AiClient, AsyncAiClient

# Use AsyncAiClient in async applications
async def async_app():
    client = AsyncAiClient()
    return await client.ask("Async question")

# Use AiClient in sync applications
def sync_app():
    client = AiClient()
    return client.ask("Sync question")

# If you need to run sync code in async context:
async def mixed_app():
    client = AsyncAiClient()
    
    # Run async code
    async_result = await client.ask("Async question")
    
    # Run sync code in async context
    sync_result = await asyncio.to_thread(lambda: AiClient().ask("Sync question"))
    
    return async_result, sync_result
```

#### Error Handling & Retries

```python
import asyncio
from ai_utilities import AsyncAiClient

async def robust_example():
    client = AsyncAiClient()
    
    prompts = ["prompt1", "prompt2", "prompt3"]
    
    # With retry logic for transient failures
    results = await client.ask_many_with_retry(
        prompts,
        concurrency=2,
        max_retries=3  # Retry up to 3 times on transient errors
    )
    
    for result in results:
        if result.error:
            print(f"Failed after retries: {result.error}")
        else:
            print(f"Success: {result.response}")

asyncio.run(robust_example())
```

### 3. 🔧 Environment Precedence System

The library uses a **clear environment precedence system** with SettingsConfigDict and contextvar-based overrides:

#### Environment Variable Precedence

**Priority Order (highest to lowest):**
1. **Init kwargs** - `AiSettings(model="custom")` overrides everything
2. **override_env contextvar** - `with override_env({"AI_MODEL": "override"})`  
3. **os.environ/.env** - Environment variables override defaults
4. **Defaults** - Fallback values in AiSettings

#### Environment Override Examples

```python
from ai_utilities import AiSettings
from ai_utilities.env_overrides import override_env

# Set base environment
import os
os.environ["AI_MODEL"] = "env-model"

# Test override_env takes precedence
with override_env({"AI_MODEL": "override-model"}):
    settings = AiSettings()
    assert settings.model == "override-model"

# After context, reverts to env value
settings = AiSettings()
assert settings.model == "env-model"

# Init kwargs override everything
settings = AiSettings(model="kw-model")
assert settings.model == "kw-model"
```

#### Environment Variable Mapping

| Environment Variable | Field | Type | Default |
|---------------------|-------|------|---------|
| `AI_API_KEY` | `api_key` | str | None |
| `AI_MODEL` | `model` | str | "gpt-4" |
| `AI_TEMPERATURE` | `temperature` | float | 0.7 |
| `AI_MAX_TOKENS` | `max_tokens` | int | None |
| `AI_BASE_URL` | `base_url` | str | None |
| `AI_TIMEOUT` | `timeout` | int | 30 |
| `AI_UPDATE_CHECK_DAYS` | `update_check_days` | int | 30 |
| `AI_USAGE_SCOPE` | `usage_scope` | str | "per_client" |
| `AI_USAGE_CLIENT_ID` | `usage_client_id` | str | None |

#### Thread-Safe Environment Overrides

```python
import threading
from ai_utilities.env_overrides import override_env

def thread_worker(model_name, results, index):
    with override_env({"AI_MODEL": model_name}):
        settings = AiSettings()
        results[index] = settings.model

# Each thread sees its own environment override
results = [None] * 3
threads = [
    threading.Thread(target=thread_worker, args=("model-1", results, 0)),
    threading.Thread(target=thread_worker, args=("model-2", results, 1)),
    threading.Thread(target=thread_worker, args=("model-3", results, 2)),
]

for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

assert results == ["model-1", "model-2", "model-3"]
```

### 4. 🏗️ Provider Architecture

The library follows a **clean provider architecture** with extensible provider pattern:

#### Provider System

```python
from ai_utilities import AiClient, AiSettings, BaseProvider
from ai_utilities.providers import OpenAIProvider

# Use default OpenAI provider
client = AiClient()

# Use explicit provider
settings = AiSettings(api_key="your-key")
provider = OpenAIProvider(settings)
client = AiClient(settings=settings, provider=provider)
```

#### Custom Provider Implementation

```python
from ai_utilities.providers.base_provider import BaseProvider

class CustomProvider(BaseProvider):
    def ask(self, prompt: str, *, return_format: str = "text", **kwargs):
        # Your custom implementation
        return f"Custom response to: {prompt}"
    
    def ask_many(self, prompts: list, *, return_format: str = "text", **kwargs):
        return [self.ask(p, return_format=return_format, **kwargs) for p in prompts]

# Use custom provider
client = AiClient(provider=CustomProvider())
response = client.ask("Hello")
```

#### JSON Mode Support

```python
from ai_utilities import AiClient

client = AiClient()

# Text response (default)
text_response = client.ask("What is AI?")

# JSON response
json_response = client.ask("List 5 AI trends as JSON", return_format="json")
print(f"Type: {type(json_response)}")  # <class 'dict'>
print(f"Data: {json_response}")

# JSON mode for multiple prompts
prompts = ["List 3 colors as JSON", "List 3 animals as JSON"]
json_responses = client.ask_many(prompts, return_format="json")
for response in json_responses:
    print(f"JSON: {response}")
```

#### Typed Responses with Pydantic

```python
from ai_utilities import AiClient
from pydantic import BaseModel
from typing import Optional

class Person(BaseModel):
    name: str
    age: int
    email: Optional[str] = None

client = AiClient()

# Get strongly-typed response
person = client.ask_typed(
    "Create a person named Alice, age 30", 
    response_model=Person
)
print(f"Name: {person.name}")
print(f"Age: {person.age}")
print(f"Email: {person.email}")

# Robust JSON parsing with repair attempts
try:
    data = client.ask_json("List 5 colors as JSON array", max_repairs=2)
    print(data)  # ["red", "blue", "green", "yellow", "orange"]
except JsonParseError as e:
    print(f"Failed to parse JSON: {e}")
```

### 5. Advanced Usage

```python
from ai_utilities import AiClient, AiSettings

# Explicit settings
settings = AiSettings(
    api_key="your-key",
    model="gpt-3.5-turbo",
    temperature=0.5
)
client = AiClient(settings)

# Disable progress indicator
client = AiClient(show_progress=False)

# Enable usage tracking
client = AiClient(track_usage=True)
stats = client.get_usage_stats()
print(f"Tokens used: {stats.tokens_used_today}")
```

### 6. 🔒 Thread-Safe Usage Tracking & ⚡ Parallel AI Calls

The library now provides **thread-safe usage tracking** with **configurable scoping** and **race condition prevention** for parallel AI calls.

#### Usage Tracking Scopes

```python
from ai_utilities import AiClient, AiSettings, UsageScope

# Per-Client Tracking (Default) - Each client has separate stats
client1 = AiClient(track_usage=True)
client2 = AiClient(track_usage=True)
# client1 and client2 maintain separate usage statistics

# Per-Process Tracking - Shared within the same process
settings = AiSettings(usage_scope="per_process")
client3 = AiClient(settings=settings, track_usage=True)
client4 = AiClient(settings=settings, track_usage=True)
# client3 and client4 share usage statistics

# Global Tracking - Shared across all processes
settings = AiSettings(usage_scope="global")
client5 = AiClient(settings=settings, track_usage=True)
# All clients with global scope share the same statistics

# Custom Client ID - Controlled sharing
settings = AiSettings(
    usage_scope="per_client",
    usage_client_id="my_app_instance"
)
client6 = AiClient(settings=settings, track_usage=True)
```

#### Parallel AI Calls with Thread Safety

```python
import concurrent.futures

# Create client with thread-safe usage tracking
client = AiClient(track_usage=True)

def make_ai_call(question):
    """Make a single AI call."""
    return client.ask(question)

# Make multiple AI calls in parallel
questions = [
    "What is the capital of France?",
    "What is the capital of Germany?",
    "What is the capital of Spain?",
    "What is the capital of Italy?"
]

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    # Submit all tasks
    futures = [executor.submit(make_ai_call, q) for q in questions]
    
    # Collect results as they complete
    results = []
    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())

print(f"Completed {len(results)} parallel calls")

# Usage statistics are accurate even with concurrent access
client.print_usage_summary()
```

#### Advanced Usage Tracking

```python
from ai_utilities import create_usage_tracker, UsageScope

# Create custom tracker with specific scope
tracker = create_usage_tracker(
    scope=UsageScope.PER_PROCESS,
    client_id="my_parallel_app"
)

# Manual usage recording
tracker.record_usage(tokens_used=150)
tracker.record_usage(tokens_used=75)

# Get statistics
stats = tracker.get_stats()
print(f"Total tokens: {stats.total_tokens}")
print(f"Total requests: {stats.total_requests}")

# Get aggregated statistics across all scopes
aggregated = tracker.get_aggregated_stats()
print(f"Found {len(aggregated)} usage tracking files")

# Reset statistics
tracker.reset_stats()
```

#### Environment Variable Configuration

```bash
# Configure usage tracking scope
export AI_USAGE_SCOPE="per_process"  # per_client, per_process, global

# Custom client ID for controlled sharing
export AI_USAGE_CLIENT_ID="my_app_instance"
```

#### Thread Safety Features

**🔒 Race Condition Prevention:**
- Cross-platform file locking with `portalocker`
- Atomic file operations with temporary files
- Thread-safe memory caching with RLock

**📊 Configurable Scoping:**
- **Per-Client**: Unique tracking per client instance
- **Per-Process**: Shared tracking within process
- **Global**: Global tracking across all processes

**⚡ Performance Optimizations:**
- Memory caching (1-second TTL) reduces file I/O
- Efficient file locking with minimal contention
- Smart directory structure in `.ai_utilities/usage_stats/`

**🛡️ Robustness:**
- Corruption handling with graceful fallbacks
- Automatic directory creation
- Cross-platform compatibility

#### Real-World Example

```python
import concurrent.futures
import time

def parallel_ai_processing():
    """Process multiple AI requests in parallel with accurate usage tracking."""
    
    # Configure for per-process tracking
    settings = AiSettings(
        api_key="your-key",
        usage_scope="per_process"
    )
    
    client = AiClient(settings=settings, track_usage=True)
    
    def process_document(doc_text):
        """Process a single document."""
        prompt = f"Summarize this document: {doc_text[:200]}..."
        return client.ask(prompt)
    
    # Simulate processing multiple documents
    documents = ["doc1.txt", "doc2.txt", "doc3.txt", "doc4.txt", "doc5.txt"]
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Process all documents in parallel
        futures = [executor.submit(process_document, doc) for doc in documents]
        summaries = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    
    print(f"Processed {len(summaries)} documents in {end_time - start_time:.2f} seconds")
    
    # Usage statistics accurately reflect all parallel calls
    client.print_usage_summary()

if __name__ == "__main__":
    parallel_ai_processing()
```

---

## API Reference

### AiSettings

Configuration settings for AI client with SettingsConfigDict and environment precedence:

```python
from ai_utilities import AiSettings

# Environment-based configuration (default)
settings = AiSettings()

# Explicit configuration
settings = AiSettings(
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.7,
    update_check_days=30  # Check for new models every 30 days
)

# Smart setup (checks for missing API key and new models)
settings = AiSettings.smart_setup()

# Force reconfiguration
settings = AiSettings.reconfigure()

# Create isolated settings with environment overrides
from ai_utilities.env_overrides import override_env
with override_env({"AI_MODEL": "gpt-3.5-turbo"}):
    settings = AiSettings()  # Uses override_env value
```

**Environment Variables:**
- `AI_API_KEY`: OpenAI API key
- `AI_MODEL`: Default model (default: "gpt-4")
- `AI_TEMPERATURE`: Response temperature (default: "0.7")
- `AI_MAX_TOKENS`: Maximum response tokens
- `AI_BASE_URL`: Custom API base URL
- `AI_TIMEOUT`: Request timeout in seconds (default: "30")
- `AI_UPDATE_CHECK_DAYS`: Days between model update checks (default: "30")
- `AI_USAGE_SCOPE`: Usage tracking scope (default: "per_client")
- `AI_USAGE_CLIENT_ID`: Custom usage tracking client ID

**Methods:**
- `interactive_setup()`: Interactive configuration prompt
- `smart_setup()`: Smart setup with model update checking
- `reconfigure()`: Force reconfiguration
- `check_for_updates(api_key, check_interval_days)`: Check for new models
- `validate_model_availability(api_key, model)`: Check if model is available in OpenAI API
- `create_isolated(env_overrides)`: Create settings with environment overrides (deprecated)

### AiClient

Main client for AI interactions with provider abstraction.

**Constructor Parameters:**
- `settings` (AiSettings, optional): Configuration settings
- `provider` (BaseProvider, optional): Custom provider
- `track_usage` (bool, default=False): Track token usage to file
- `usage_file` (Path, optional): Custom usage tracking file
- `show_progress` (bool, default=True): Show progress indicator during requests
- `auto_setup` (bool, default=True): Auto-prompt if API key missing
- `smart_setup` (bool, default=False): Smart setup with model updates

**Methods:**
- `ask(prompt, return_format="text", **kwargs)`: Ask single question
- `ask_many(prompts, return_format="text", **kwargs)`: Ask multiple questions
- `ask_json(prompt, **kwargs)`: Ask question with JSON response
- `check_for_updates(force_check=False)`: Check for new models (returns detailed info)
- `reconfigure()`: Force reconfiguration of settings
- `get_usage_stats()`: Get usage statistics if tracking enabled
- `print_usage_summary()`: Print usage summary if tracking enabled

**Return Format Options:**
- `"text"`: Returns string response (default)
- `"json"`: Returns dictionary response with JSON parsing

### AsyncAiClient

Asynchronous client for AI interactions with concurrency control.

**Constructor Parameters:**
- Same as AiClient

**Methods:**
- `ask(prompt, return_format="text", **kwargs)`: Ask single question (async)
- `ask_many(prompts, concurrency=3, on_progress=None, return_format="text", **kwargs)`: Ask multiple questions with concurrency control
- `ask_many_with_retry(prompts, concurrency=3, max_retries=3, on_progress=None, return_format="text", **kwargs)`: Ask with retry logic

### Provider Classes

#### BaseProvider

Abstract base class for implementing custom providers.

**Methods to Implement:**
- `ask(prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, dict]`
- `ask_many(prompts: list, *, return_format: str = "text", **kwargs) -> List[Union[str, dict]]`

#### OpenAIProvider

OpenAI-specific provider implementation.

**Features:**
- Native JSON mode support for compatible models
- Automatic model detection for JSON capabilities
- Fallback JSON extraction for older models
- Rate limit handling and retry logic

### Environment Override System

#### override_env Context Manager

Thread-safe contextvar-based environment overrides.

```python
from ai_utilities.env_overrides import override_env

# Override environment for specific context
with override_env({"AI_MODEL": "gpt-3.5-turbo", "AI_TEMPERATURE": "0.5"}):
    client = AiClient()
    response = client.ask("What is AI?")  # Uses overridden settings

# Environment automatically restored after context
```

**Features:**
- Thread-safe using contextvars
- Nested context support with merging
- No mutation of os.environ
- Async and thread safe

### Usage Tracking

#### UsageTracker

Optional usage tracking for monitoring API consumption.

**Features:**
- Daily and total token/request tracking
- Persistent storage to JSON file
- Automatic daily reset
- Usage summary reporting
- Thread-safe with configurable scoping

**Scopes:**
- `"per_client"`: Unique tracking per client instance (default)
- `"per_process"`: Shared tracking within process
- `"global"`: Global tracking across all processes

---

## Examples

Below are some runnable examples using the new v1 API.

### 1. Single Prompt Example

```python
from ai_utilities import AiClient

def main() -> None:
    # Using environment variables
    client = AiClient()
    
    response = client.ask("What is the capital of France?")
    print(f"Answer: {response}")

if __name__ == "__main__":
    main()
```

### 2. Multiple Prompts Example

```python
from ai_utilities import AiClient

def main() -> None:
    client = AiClient()
    
    prompts = [
        "What is the capital of France?",
        "What is the largest planet in our solar system?",
        "Who wrote Romeo and Juliet?"
    ]
    
    responses = client.ask_many(prompts)
    
    for prompt, response in zip(prompts, responses):
        print(f"Q: {prompt}")
        print(f"A: {response}\n")

if __name__ == "__main__":
    main()
```

### 3. JSON Response Example

```python
from ai_utilities import AiClient

def main() -> None:
    client = AiClient()
    
    response = client.ask_json("List 5 AI trends as JSON")
    print(f"JSON Response: {response}")

if __name__ == "__main__":
    main()
```

### 4. Usage Tracking Example

```python
from ai_utilities import AiClient

def main() -> None:
    # Enable usage tracking
    client = AiClient(track_usage=True)
    
    # Make some requests
    client.ask("What is AI?")
    client.ask("Explain machine learning")
    
    # Get usage statistics
    stats = client.get_usage_stats()
    print(f"Today's requests: {stats.requests_today}")
    print(f"Today's tokens: {stats.tokens_used_today}")
    
    # Print summary
    client.print_usage_summary()

if __name__ == "__main__":
    main()
---

## 🏗️ Architecture

The library follows a **clean provider architecture** with **Pydantic-based configuration** and **environment precedence system**.

### Component Architecture

```
ai_utilities/
├── 📋 client.py                    # Main client interface
│   ├── AiClient                    # High-level API with provider abstraction
│   ├── AsyncAiClient               # Asynchronous client interface
│   └── AiSettings                  # Pydantic settings with SettingsConfigDict
├── 🔌 providers/                   # Provider system
│   ├── base_provider.py            # Abstract provider interface
│   ├── openai_provider.py          # OpenAI provider implementation
│   └── __init__.py                 # Provider exports
├── 🌍 env_overrides.py             # Thread-safe environment overrides
│   └── override_env                # Contextvar-based environment manager
├── 📊 usage_tracker.py             # Thread-safe usage tracking
│   ├── UsageTracker                # Usage tracking implementation
│   ├── ThreadSafeUsageTracker      # Concurrent-safe tracking
│   └── create_usage_tracker        # Factory function
├── 📈 rate_limit_fetcher.py        # Dynamic rate limit system
│   ├── RateLimitFetcher            # API-based limit detection
│   └── RateLimitInfo               # Rate limit data structure
├── ⏱️ progress_indicator.py        # Progress display system
├── 🔢 token_counter.py             # Token counting utilities
├── 📋 models.py                    # Data models
│   └── AskResult                   # Response data structure
└── 🛠️ utilities/                   # Supporting utilities
    ├── env_utils.py                # Environment utilities
    ├── error_codes.py              # Error definitions
    └── exceptions.py               # Custom exceptions
```

### Design Principles

**🔧 Type-Safe Configuration**
- Pydantic SettingsConfigDict with validation
- Environment variable integration with clear precedence
- SettingsConfigDict for pydantic-settings compliance

**🏗️ Provider Architecture**
- Clean provider abstraction with BaseProvider interface
- OpenAIProvider with JSON mode and retry logic
- Extensible for future provider implementations

**🌍 Environment Precedence System**
- Clear priority: init kwargs > override_env > os.environ > defaults
- Thread-safe contextvar-based overrides
- No mutation of os.environ

**🔒 Thread Safety**
- Contextvar-based environment overrides
- Thread-safe usage tracking with file locking
- Concurrent access protection for shared resources

**⚡ Performance Optimizations**
- Efficient provider protocol with minimal overhead
- Smart JSON mode detection and fallback
- Memory caching for frequently accessed data

### Provider Protocol

The library uses a standardized provider protocol:

```python
class BaseProvider:
    def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, dict]:
        """Ask a single question."""
        
    def ask_many(self, prompts: list, *, return_format: str = "text", **kwargs) -> List[Union[str, dict]]:
        """Ask multiple questions."""
```

**Return Format Support:**
- `"text"`: Returns string response
- `"json"`: Returns dictionary with parsed JSON

### Environment Precedence Flow

```
Init kwargs (highest priority)
    ↓
override_env contextvar
    ↓  
os.environ / .env files
    ↓
Default values (lowest priority)
```

### Usage Tracking Architecture

```
UsageTracker
├── ThreadSafeUsageTracker     # Concurrent-safe implementation
├── File-based persistence     # JSON storage with locking
├── Configurable scoping       # per_client, per_process, global
└── Memory caching             # 1-second TTL for performance
```
- Each component has one well-defined purpose
- Clean composition instead of monolithic classes
- Testable and maintainable architecture

**📊 Dynamic Rate Management**
- Automatic OpenAI rate limit detection
- API credit conservation with smart caching
- Fallback to known defaults when API unavailable

**🛡️ Error Handling & Validation**
- Comprehensive Pydantic validation
- Graceful fallbacks and error recovery
- Detailed error messages and logging

### Data Flow

```
Environment Variables → Pydantic Models → AIConfigManager → AiClient
                                     ↓
RateLimitFetcher → Dynamic Limits → Component Orchestration → API Response
```

### Configuration Layers

1. **Developer Defaults** - Base Pydantic model defaults
2. **Environment Variables** - Runtime overrides with validation
3. **Dynamic Rate Limits** - API-fetched limits (30-day cache)
4. **Programmatic Override** - Direct Python configuration

### Component Interactions

**OpenAIModel Composition:**
```python
OpenAIModel
├── OpenAIClient      # API communication
├── ResponseProcessor # Response processing
├── TokenCounter      # Token counting
└── RateLimiter       # Rate limiting
```

**AIConfigManager Integration:**
```python
AIConfigManager
├── Pydantic Models   # Type-safe configuration
├── RateLimitFetcher # Dynamic rate limits
└── File Management   # Config persistence
```

---

## Testing

The library includes **comprehensive test coverage** with **118+ tests** covering all major architectural changes:

### Test Coverage Overview

The library has comprehensive test coverage with **233 passing tests** covering all major functionality:

- ✅ **AiSettings Configuration** (50+ tests) - SettingsConfigDict, environment precedence, validation
- ✅ **Environment Override System** (16+ tests) - override_env contextvar, thread safety, precedence
- ✅ **Provider Protocol** (35+ tests) - BaseProvider interface, OpenAIProvider, JSON mode
- ✅ **Client Functionality** (40+ tests) - AiClient, AsyncAiClient, ask/ask_many methods
- ✅ **Usage Tracking** (30+ tests) - ThreadSafeUsageTracker, scoping, concurrent access
- ✅ **Rate Limit Fetching** (25+ tests) - Dynamic rate limits, caching, error handling
- ✅ **Progress Indicators** (15+ tests) - Progress display, timing, cancellation
- ✅ **Token Counting** (20+ tests) - Multi-method counting, model-specific algorithms
- ✅ **Error Handling** (12+ tests) - Custom exceptions, validation, retry logic

**Test Categories:**
- **Unit Tests**: Individual component testing with mocking
- **Integration Tests**: End-to-end functionality testing
- **Concurrency Tests**: Thread safety and async behavior
- **Environment Tests**: Contextvar isolation and precedence
- **Protocol Tests**: Provider interface compliance
- **Performance Tests**: Rate limiting and caching behavior

**Running Tests:**
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_settings_precedence.py  # Environment precedence
pytest tests/test_provider_protocol.py     # Provider interface
pytest tests/test_env_overrides.py         # Environment overrides
pytest tests/test_usage_tracking.py        # Usage tracking

# Run only fast tests (exclude slow tests)
pytest -m "not slow"

# Run only slow tests (thread safety, concurrency tests)
pytest -m slow
```

**Slow Tests:**
Some tests are marked with `@pytest.mark.slow` for better CI/CD performance:

- **Thread Safety Tests** - Concurrent execution with multiple threads
- **Async Safety Tests** - Task coordination and context isolation
- **Concurrency Tests** - High-contention scenarios

This allows developers to run fast tests frequently during development and run slow tests selectively or in CI/CD pipelines.

### Running Tests

```bash
# Install development dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_config_models.py -v          # Pydantic configuration tests
pytest tests/test_single_responsibility_refactoring.py -v  # SRP component tests
pytest tests/test_rate_limit_fetching.py -v    # Dynamic rate limit tests
pytest tests/test_ai_config_manager.py -v      # Configuration manager tests
pytest tests/test_thread_safe_usage_tracking.py -v  # Thread-safe usage tracking tests

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=ai_utilities --cov-report=html
```

### Test Categories

**🔧 Pydantic Configuration Tests:**
- Model validation and constraints
- Environment variable integration
- Configuration immutability
- Error handling and validation

**🏗️ Single Responsibility Tests:**
- OpenAIClient API communication
- ResponseProcessor text processing
- TokenCounter counting algorithms
- Component composition and integration

**📊 Dynamic Rate Limit Tests:**
- Rate limit fetching from OpenAI API
- 30-day cache behavior and expiration
- Fallback mechanisms and error handling
- API credit conservation

**⚙️ Configuration Manager Tests:**
- Pydantic configuration management
- Dynamic rate limit integration
- File loading and saving
- Environment variable precedence

**🔒 Thread-Safe Usage Tracking Tests:**
- Concurrent usage recording with multiple threads
- Race condition prevention and file locking
- Scope isolation (per-client, per-process, global)
- Memory caching and performance optimization
- File corruption handling and recovery
- High-concurrency stress testing (50+ threads)

### Test Quality Features

- **Mock Integration**: Comprehensive mocking for external APIs
- **Error Scenarios**: Robust failure and edge case testing
- **Performance Testing**: Cache behavior and optimization
- **Integration Testing**: End-to-end workflow validation
- **Type Safety**: Pydantic validation testing

```bash
# Test configuration system
pytest tests/test_settings.py

# Test client functionality
pytest tests/test_client.py

# Test usage tracking
pytest tests/test_usage_tracking.py

# Test progress indicator
pytest tests/test_progress_indicator.py
```

All tests use the `FakeProvider` for offline testing - no API key required.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v --cov=ai_utilities
```

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

---

## 📋 Changelog

### v0.4.0 - Provider Support & Local AI

**🌐 Multi-Provider Support:**
- ✅ **OpenAI-Compatible Provider**: First-class support for local AI servers (Ollama, vLLM, LM Studio, etc.)
- ✅ **Provider Factory**: Automatic provider selection based on configuration
- ✅ **Same API**: `AiClient.ask()` works identically across all providers
- ✅ **Configuration-Driven**: Switch providers via `AI_PROVIDER` environment variable or settings

**🔧 New Configuration Options:**
- `AI_PROVIDER`: Choose between "openai" (default) and "openai_compatible"
- `AI_BASE_URL`: Required for openai_compatible provider (e.g., `http://localhost:11434/v1`)
- `AI_REQUEST_TIMEOUT_S`: Float timeout for precise control
- `AI_EXTRA_HEADERS`: Custom headers for gateways and authentication

**🛡️ Enhanced Error Handling:**
- `ProviderConfigurationError`: Clear errors for missing/invalid provider setup
- `ProviderCapabilityError`: Informative errors for unsupported features
- Graceful degradation for local server limitations

**📦 New Exports:**
- `OpenAICompatibleProvider`: Local server provider implementation
- `create_provider()`: Provider factory function
- `ProviderCapabilities`: Provider feature discovery
- `ProviderCapabilityError`, `ProviderConfigurationError`: Custom exceptions

**🧪 Comprehensive Testing:**
- 30 new tests covering provider selection, configuration, and error handling
- Mocked network calls for reliable testing
- Full backward compatibility verification

**📚 Updated Documentation:**
- Provider configuration examples for popular local servers
- Vendor-neutral "OpenAI-compatible" terminology
- Migration guide from OpenAI to local providers
- Advanced configuration examples with custom headers

**🔄 Backward Compatibility:**
- ✅ Existing OpenAI usage unchanged - zero migration required
- ✅ All existing APIs work identically
- ✅ Default provider remains OpenAI for seamless upgrades

---

## License

MIT License - see LICENSE file for details.

---


**Cache Location:** `~/.ai_utilities_model_cache.json`

**Cache Behavior:**
- **Automatic Caching**: Results cached after each successful model check
- **Configurable Interval**: Default 30 days, adjustable via `AI_UPDATE_CHECK_DAYS`
- **Cost Optimization**: Cached results are free, fresh checks consume tokens
- **Force Refresh**: Use `force_check=True` to bypass cache when needed
- **Cache Status**: Update info includes `cached: True/False` field

**Cache Contents:**
```json
{
  "last_check": "2025-12-23T08:30:00",
  "has_updates": true,
  "new_models": ["gpt-4o", "gpt-4o-mini"],
  "current_models": ["gpt-4", "gpt-3.5-turbo", ...],
  "total_models": 47
}
```

**Environment Configuration:**
```bash
# Check for updates every 7 days instead of 30
export AI_UPDATE_CHECK_DAYS=7

# Disable automatic checking (manual only)
export AI_UPDATE_CHECK_DAYS=999
```

---

pytest tests/
```

Run specific test categories:

```bash
# Test configuration system
pytest tests/test_settings.py

# Test client functionality
pytest tests/test_client.py

# Test usage tracking
pytest tests/test_usage_tracking.py

# Test progress indicator
pytest tests/test_progress_indicator.py
```

All tests use the `FakeProvider` for offline testing - no API key required.

---

## 🛡️ Provider Health Monitoring

AI Utilities includes a comprehensive provider health monitoring system to detect issues before they affect your applications.

### 🚀 Quick Health Check

```bash
# Daily health check
python scripts/daily_provider_check.py

# Comprehensive analysis
python scripts/provider_change_detector.py

# Run monitoring tests
pytest tests/provider_monitoring/ -v
```

### 📊 What's Monitored

| Provider | Status | Response Time | Model Availability |
|----------|--------|---------------|-------------------|
| **OpenAI** | ✅ Monitored | ✅ Tracked | ✅ Validated |
| **Groq** | ✅ Monitored | ✅ Tracked | ✅ Validated |
| **Together AI** | ✅ Monitored | ✅ Tracked | ✅ Validated |
| **OpenRouter** | ✅ Monitored | ✅ Tracked | ✅ Validated |
| **Ollama** | ✅ Monitored | ✅ Tracked | ✅ Validated |
| **LM Studio** | ✅ Monitored | ✅ Tracked | ✅ Validated |

### 🔧 Monitoring Features

- **🔍 Change Detection** - Automatically detects API changes, model removals, and service issues
- **📈 Performance Tracking** - Monitors response times and availability
- **🚨 Alert System** - Generates detailed reports for any issues
- **🔄 CI/CD Integration** - Automated monitoring in GitHub Actions
- **🧪 Bug Prevention** - Comprehensive tests prevent regressions

### 📋 Monitoring Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `daily_provider_check.py` | Simple daily health check | `python scripts/daily_provider_check.py` |
| `provider_health_monitor.py` | Comprehensive monitoring | `python scripts/provider_health_monitor.py` |
| `provider_change_detector.py` | Change detection & analysis | `python scripts/provider_change_detector.py` |
| `ci_provider_check.sh` | CI/CD integration | `./scripts/ci_provider_check.sh` |

### 🎯 Example Output

```
🌅 DAILY PROVIDER HEALTH CHECK
========================================
🔍 Checking OpenAI...
   ✅ Status: HEALTHY
   ⏱️  Response time: 1.57s
   🤖 Model: gpt-3.5-turbo

🔍 Checking Groq...
   ✅ Status: HEALTHY
   ⏱️  Response time: 0.51s
   🤖 Model: llama-3.1-8b-instant

📊 SUMMARY: 6/6 providers healthy
✅ All providers healthy - no action needed!
```

### 🔄 Automated Monitoring

Add to your GitHub Actions (`.github/workflows/provider-health.yml`):

```yaml
name: Provider Health Monitor
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:       # Manual trigger

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run health check
      run: python scripts/daily_provider_check.py
```

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/provider_monitoring/ -v  # Provider monitoring tests
pytest tests/integration/ -v          # Integration tests
pytest tests/demo/ -v                 # Demo app tests
```

### 📊 Test Coverage

- **🛡️ Bug Prevention Tests** - Prevent regressions of known issues
- **🔍 Integration Tests** - Real provider connectivity
- **🧪 Unit Tests** - Core functionality validation
- **📋 Provider Tests** - All 6 providers tested

### 🎯 Test Categories

| Category | Purpose | Command |
|----------|---------|---------|
| **Bug Prevention** | Prevent regressions | `pytest tests/provider_monitoring/test_critical_bugs.py` |
| **Integration** | Real API testing | `pytest tests/integration/ -v` |
| **Monitoring** | Health system tests | `pytest tests/provider_monitoring/ -v` |
| **Core Library** | Main functionality | `pytest tests/test_*.py` |

---

## Migration from config.ini

If you're migrating from the old config.ini approach:

1. **Replace config.ini with environment variables:**
   ```ini
   # Old config.ini
   [openai]
   model = gpt-4
   api_key = your-key
   
   # New environment variables
   export AI_MODEL="gpt-4"
   export AI_API_KEY="your-key"
   ```

2. **Update your code:**
   ```python
   # Old approach
   from ai_utilities.ai_integration import ask_ai
   response = ask_ai("your prompt")
   
   # New approach
   from ai_utilities import AiClient
   client = AiClient()
   response = client.ask("your prompt")
   ```

3. **Optional: Use explicit config loading:**
   ```python
   from ai_utilities import AiSettings, AiClient
   
   # Explicitly load from config file (not automatic)
   settings = AiSettings.from_ini("config.ini")
   client = AiClient(settings)
   ```

---

## 📋 Changelog

### 🛡️ Provider Health Monitoring (Latest)
- **✅ Added comprehensive provider monitoring system** - Detect issues before they affect users
- **🔍 Change detection** - Automatic detection of API changes, model removals, and service issues
- **📈 Performance tracking** - Monitor response times and availability across all providers
- **🚨 Alert system** - Detailed reports and recommendations for any issues
- **🔄 CI/CD integration** - Automated monitoring with GitHub Actions
- **🧪 Bug prevention tests** - 17 comprehensive tests prevent regressions

### 🔧 Critical Bug Fixes
- **🔑 Fixed API headers issue** - Resolved 401 errors for OpenAI, Groq, and Together AI
- **📋 Fixed response parsing** - Added proper handling for Together AI list responses
- **🏗️ Improved project organization** - Clean separation of source code, tests, and scripts
- **🧪 Enhanced test coverage** - Added focused bug prevention tests

### 📊 New Monitoring Scripts
- `daily_provider_check.py` - Simple daily health check
- `provider_health_monitor.py` - Comprehensive monitoring system
- `provider_change_detector.py` - Change detection and analysis
- `ci_provider_check.sh` - CI/CD integration script

### 🎯 Provider Support
- **✅ OpenAI** - Full monitoring and testing
- **✅ Groq** - Full monitoring and testing  
- **✅ Together AI** - Full monitoring and testing
- **✅ OpenRouter** - Full monitoring and testing
- **✅ Ollama** - Local server monitoring
- **✅ LM Studio** - Local server monitoring

---

## 📞 Support & Contributing

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/audkus/ai_utilities/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/audkus/ai_utilities/discussions)
- 📧 **Questions**: Open a GitHub Discussion
- 🔧 **Contributing**: See [Contributing Guide](CONTRIBUTING.md)

---

**⭐ If you find AI Utilities helpful, please give it a star on GitHub!**
---
