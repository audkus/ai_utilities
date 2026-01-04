# Manual Testing Harness

This directory contains manual testing scripts for pre-release verification of AI Utilities.

## Purpose

These tests are designed for manual verification before releases and are NOT intended for:
- CI/CD pipelines
- Automated testing
- Import validation

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
