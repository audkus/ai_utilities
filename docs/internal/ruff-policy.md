# Ruff Policy

This document governs Ruff linting configuration for the ai_utilities project.

## Configuration Philosophy

- **Strict by default**: Enable comprehensive linting rules
- **Minimal exceptions**: Only ignore rules when absolutely necessary
- **Documented exceptions**: Every ignore must have explicit justification
- **No silent drift**: Policy tests prevent configuration changes without review

## Rule Categories

### Enabled Rules (`select`)

- **E, W**: pycodestyle - Code formatting and style consistency
- **F**: Pyflakes - Undefined names, unused imports, basic errors
- **UP**: pyupgrade - Modern Python patterns (with compatibility exceptions)
- **B**: flake8-bugbear - Common programming pitfalls and anti-patterns
- **SIM**: flake8-simplify - Code simplification opportunities
- **I**: isort - Import organization and consistency
- **S**: flake8-bandit - Security issues and vulnerabilities
- **RUF**: ruff-specific - Performance and style improvements
- **C4**: flake8-comprehensions - Better comprehension patterns
- **PIE**: flake8-pie - Miscellaneous code improvements

### Global Ignores (`ignore`)

| Rule | Justification |
|------|---------------|
| F403/F405 | Star imports necessary for `__init__.py` dynamic loading patterns |
| UP006/UP045/UP007 | Typing modernization deferred for Python 3.9 compatibility |

## Per-File Exceptions

### Development Tools

| Pattern | Rules | Justification |
|---------|-------|---------------|
| `dev_tools/**` | S101 | Assert statements acceptable in internal development tools |
| `tools/diagnostics/**` | S101 | Assert statements useful for diagnostic scripts |
| `tools/benchmarks.py` | F841, E501, F401, UP006, UP035, RUF059 | Benchmark-specific patterns: unused variables for measurements, long lines for output formatting, conditional imports, legacy typing for compatibility |

### Test Files

| Pattern | Rules | Justification |
|---------|-------|---------------|
| `tests/utils/**` | UP006, UP035, F841, W293 | Test utilities: legacy typing for compatibility, unused variables in setup, whitespace for readability |
| `tests/**` | S101, B018, S105, S106, S108, S311, S603, S607, B011, B017, E501, SIM117, SIM105 | Test environment: assert statements expected, fake credentials, temporary files, deterministic randomness, controlled subprocess calls, long lines for readability, multiple context managers, exception suppression for control flow |

### Source Code

| Pattern | Rules | Justification |
|---------|-------|---------------|
| `src/ai_utilities/cli.py` | (none) | CLI tools appropriately use print statements |
| `src/ai_utilities/client.py` | E402 | Conditional imports for optional OpenAI dependency handling |
| `src/ai_utilities/providers/openai_provider.py` | E402 | Conditional imports for optional OpenAI dependency |
| `src/ai_utilities/providers/openai_compatible_provider.py` | E402 | Conditional imports for optional OpenAI dependency |
| `src/ai_utilities/cache.py` | S608 | SQL queries use validated table names (safe context) |
| `src/ai_utilities/_test_reset.py` | S110 | Try-except-pass acceptable for test cleanup operations |
| `src/ai_utilities/audio/audio_utils.py` | S110 | Try-except-pass for audio error handling patterns |
| `src/ai_utilities/setup/**` | (none) | Setup tools appropriately use print statements |
| `src/ai_utilities/__init__.py` | F401, E402 | Dynamic loading patterns and module organization |
| `src/ai_utilities/knowledge/models.py` | S607 | Git subprocess calls in safe, controlled context |

## Change Process

### Making Changes

1. **Fix the code first** - Always prefer fixing code over adding ignores
2. **Update the policy test** - Modify `tests/test_policy_no_new_ruff_ignores.py`
3. **Update this documentation** - Add justification for new exceptions
4. **Update the justification date** - Change the date in the test file

### Forbidden Changes

- ❌ Adding ignores to silence legitimate issues (F841, UP0xx, etc.)
- ❌ Blanket per-file ignores without specific rule justification
- ❌ Relaxing security rules without documented necessity
- ❌ Adding ignores for convenience rather than necessity

### Review Process

Any Ruff configuration changes require:
1. Technical justification in this document
2. Policy test baseline update
3. Code review approval
4. CI verification

## Enforcement

The policy test `tests/test_policy_no_new_ruff_ignores.py` enforces these rules:

- ✅ Configuration changes require test baseline updates
- ✅ Justification must be documented
- ✅ Policy documentation must exist and be current
- ❌ Silent configuration drift is impossible

## Last Updated

**Date:** 2025-01-25  
**Version:** 1.0  
**Enforced by:** `tests/test_policy_no_new_ruff_ignores.py`

---

*This policy is non-negotiable. Changes require explicit justification and approval.*
