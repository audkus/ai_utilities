# Manual Testing Harness

This directory contains manual testing scripts for pre-release verification of AI Utilities.

## Purpose

These tests are designed for manual verification before releases and are NOT intended for:
- CI/CD pipelines
- Automated testing
- Import validation

## Available Scripts

### debug_standard_setup.py
**Purpose**: Debug and verify the enhanced tiered setup system functionality

**What it tests**:
- Standard setup flow with mocked inputs
- Boolean input handling (case insensitive, whitespace tolerant)
- Cache parameter configuration
- update_check_days parameter functionality
- .env file generation with proper permissions
- All Standard Setup tier features

**Usage**:
```bash
python manual_tests/debug_standard_setup.py
```

**Expected Output**:
- ✅ Setup completed successfully
- ✅ cache_enabled: True
- ✅ cache_backend: sqlite
- ✅ AI_CACHE_ENABLED found in .env
- ✅ All 11 config keys properly configured

### minimal_test.py
**Purpose**: Test provider installation help functionality

**What it tests**:
- Provider help text generation
- Installation command formatting
- Component presence verification
- String matching accuracy

**Usage**:
```bash
python manual_tests/minimal_test.py
```

**Expected Output**:
- ✅ Generated help text contains all providers
- ✅ Installation commands properly formatted
- ✅ All key components found (pip, install, ai-utilities, openai, groq)

## Test Structure

### Tier 1 Tests (All Providers, No Network)
- Validates provider configuration and error handling
- Runs without requiring API keys or network access
- Tests all supported providers for basic functionality

### Tier 2 Tests (OpenAI Only, Real Calls)
- End-to-end testing with actual API calls
- Requires valid API keys
- Default provider: OpenAI only

## Usage

```bash
# Debug tiered setup system
python manual_tests/debug_standard_setup.py

# Test provider installation help
python manual_tests/minimal_test.py

# Run Tier 1 tests (all providers, no network)
./run_manual_tests.sh

# Run Tier 1 + Tier 2 (OpenAI with real calls)
./run_manual_tests.sh --tier2

# Run Tier 2 for specific provider
./run_manual_tests.sh --tier2 --provider openai

# Run with custom timeout
./run_manual_tests.sh --timeout 60
```

## Requirements

- Tier 1: No requirements (runs in isolated environment)
- Tier 2: `AI_API_KEY` environment variable set

## Output

Results are saved to `reports/manual_report_*.md` files.

## Safety

- Creates isolated virtual environments
- No prompts or interactive input
- All network calls are opt-in
- Outputs are gitignored

See [../RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) for detailed release procedures.
