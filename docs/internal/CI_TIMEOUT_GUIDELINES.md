# CI Timeout Guard Rails

This document describes the timeout configuration for CI/CD pipelines to prevent hanging tests.

## Timeout Configuration

### Unit Tests (Fast, Strict)
- **Timeout**: 30 seconds per test
- **Command**: `pytest -m "not integration" --timeout=30`
- **Expected Duration**: ~10 minutes total
- **Purpose**: Fast feedback on code changes

### Integration Tests (Slower, Bounded)
- **Timeout**: 120 seconds per test
- **Command**: `pytest -m "integration" --timeout=120`
- **Expected Duration**: ~25 minutes total
- **Purpose**: Test real API interactions
- **Prerequisites**: Requires API keys/secrets

## CI Job Configuration

### GitHub Actions Example

```yaml
name: Tests

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run unit tests
        run: |
          pytest -m "not integration" --timeout=30 --cov=ai_utilities

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    if: secrets.AI_API_KEY
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -e ".[dev,providers]"
      - name: Run integration tests
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
        run: |
          pytest -m "integration" --timeout=120 --cov=ai_utilities
```

## Test Markers

### Available Markers
- `@pytest.mark.integration`: Tests that call external services
- `@pytest.mark.openai`: Tests requiring OpenAI API access
- `@pytest.mark.slow`: Tests that take longer to run

### Integration Test Requirements
Integration tests must:
1. Be marked with `@pytest.mark.integration`
2. Skip gracefully if API keys are missing:
   ```python
   @pytest.mark.skipif(
       not os.getenv("AI_API_KEY"),
       reason="Requires AI_API_KEY environment variable"
   )
   ```
3. Use higher timeout (120s) via marker or separate invocation

## Environment Variables

### Required for Integration Tests
- `AI_API_KEY`: OpenAI API key or compatible provider key
- `AI_BASE_URL`: Optional custom base URL for local testing
- `AI_TIMEOUT`: Optional custom timeout in seconds (default: 30)

### Optional Overrides
- `AI_REQUEST_TIMEOUT_S`: Float timeout override (alias for timeout)

## Failure Modes

### Timeout Failures
- Tests fail fast with clear timeout error messages
- No hanging CI jobs
- Stack trace shows which test timed out

### Missing Credentials
- Integration tests skip with clear reason
- Unit tests run regardless of credentials
- CI job fails fast if secrets unavailable

## Local Development

### Run Unit Tests Only
```bash
pytest -m "not integration" --timeout=30
```

### Run Integration Tests
```bash
export AI_API_KEY="your-api-key"
pytest -m "integration" --timeout=120
```

### Run All Tests
```bash
pytest --timeout=30  # Unit tests get 30s, integration tests need separate run
```

## Configuration Details

### Pytest Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
addopts = [
    "--timeout=30",           # Default timeout for all tests
    "--timeout-method=thread", # Use thread-based timeout
]
markers = [
    "integration: marks tests as integration tests that require real network/API calls",
]
```

### Request-Level Timeouts
OpenAI clients use configurable request timeouts:
- Default: 30 seconds
- Configurable via `AI_TIMEOUT` environment variable
- Applied at client initialization, prevents network hangs

## Success Criteria

✅ No hanging tests in CI
✅ Unit tests complete within 10 minutes
✅ Integration tests complete within 25 minutes  
✅ Clear timeout error messages
✅ Graceful handling of missing credentials
✅ No production behavior changes
