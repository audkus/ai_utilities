# Tooling Configuration

This document captures intentional decisions and known limitations in the project's tooling setup.

## Coverage Configuration

**Output Location**: `coverage_reports/html`
- Single source of truth: `pyproject.toml [tool.coverage.*]`
- Branch coverage enabled (`branch = true`)
- HTML reports generated to `coverage_reports/html` via pytest.ini

## Known Warnings

### urllib3 LibreSSL Warning
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
```

**Cause**: macOS system Python uses LibreSSL instead of OpenSSL
**Impact**: Warning only - no functional impact
**Resolution**: Use Python with OpenSSL linkage (e.g., Homebrew Python, pyenv)

## Mypy Technical Debt

**Intentional Limitations**: The following modules have `ignore_errors = true`:
- `ai_utilities.client.*` - Complex async client with conditional imports
- `ai_utilities.async_client.*` - Async patterns need typing migration  
- `ai_utilities.knowledge.*` - Knowledge base modules need architectural review
- `ai_utilities.audio.*` - Audio processing modules need gradual typing

**Future Intent**: Gradual migration to full type safety as modules are refactored.

## Ruff Configuration

**Rule Selection**: Conservative, production-grade ruleset
- Core: E, W, F (pycodestyle, warnings, pyflakes)
- Modernization: UP (pyupgrade, limited for py39 compatibility)
- Security: S (bandit, with test-specific allowances)
- Quality: B, SIM, I, RUF, C4, PIE (bugbear, simplify, isort, ruff, comprehensions, pie)

**Test Per-File Ignores**: Documented risk assessments
- `S603`, `S607`: Subprocess calls in tests (controlled inputs)
- `B017`: Assert blind exceptions in tests (pytest.raises pattern)

## Repository Hygiene

**Root Directory**: Strict allowlist enforcement via `tests/conftest.py`
- Files: 22 allowed files (config, docs, build files)
- Directories: 15 allowed directories (src, tests, docs, tools, reports)

**Test Isolation**: 
- Working directory: `tmp_path` for all tests
- Write prevention: Repository root writes blocked
- Allowed outputs: `reports/`, `coverage_reports/`

## Validation Commands

These commands must pass without modification:
```bash
ruff check .                    # Linting
python -m pytest -q -ra        # Basic test run
python -m pytest -q -W error::pytest.PytestUnraisableExceptionWarning -W error::RuntimeWarning  # Strict validation
```
