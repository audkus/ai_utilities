# AI Contribution Contract

This document defines non-negotiable rules for AI-assisted contributions
(ChatGPT, WindSurf, Codex, etc.) to ai-utilities.

Any change that violates this contract is considered incorrect,
even if tests pass, CI is green, or behavior "appears to work".

## 1. Scope

This contract applies to all AI-generated or AI-modified changes, including:

- Production code
- Tests
- Packaging and build configuration
- CI/CD workflows
- Documentation that describes behavior

Humans may override these rules explicitly.
AI tools must not.

## 2. Core Design Principles (Must Be Preserved)

### 2.1 Minimal base installation

The following must always be true:

```bash
pip install ai-utilities
python -c "import ai_utilities"
ai-utilities --help
```

Must succeed in a clean virtual environment

Must NOT require optional dependencies

Must NOT trigger provider imports, IO, or network access

Optional providers (OpenAI, Ollama, Groq, etc.) remain optional.

### 2.2 No import-time side effects

At module import time (`import ai_utilities`):

AI must not introduce:

- Network calls
- File system writes
- Environment resolution
- Provider initialization
- Optional dependency imports
- Silent fallbacks or hidden defaults

Lazy imports are required for provider-specific logic.

### 2.3 Contract-first testing

Tests describe observable behavior, not implementation details.

AI must:

- Fix tests before changing production code unless instructed otherwise
- Avoid asserting on AI-generated text or provider output
- Prefer schema, shape, and contract validation

Tests that "pass but test nothing" are invalid.

## 3. Anti-Fake-Implementation Rules (Critical)

AI tools have a known failure mode:
producing code that looks correct but does nothing.

This is explicitly forbidden.

### 3.1 No stub implementations

AI must not:

- Return constant values without justification
- Add empty functions or pass blocks
- Catch exceptions and ignore them
- Log instead of performing required logic
- Add TODOs presented as finished work

Every implementation must have observable effects.

### 3.2 Every new behavior must be falsifiable

If AI adds or modifies behavior, at least one of the following must exist:

- A test that fails if the behavior is removed
- A runtime check that raises a clear error if misused
- A documented contract enforced by code

Code that cannot be proven to run is considered dead code.

### 3.3 "Looks implemented" is not implemented

The following patterns are not acceptable:

- Wrapper functions that only forward arguments without validation
- Configuration flags that are never read
- Feature toggles without call sites
- CLI options that are parsed but unused
- Error messages without corresponding error paths

If a feature is claimed, it must execute.

## 4. Packaging & Distribution Rules (Release-Critical)

### 4.1 Wheel install is the source of truth

AI must assume users install from wheels, not editable checkouts.

All packaging changes must pass:

```bash
python -m build
pip install dist/*.whl
python -c "import ai_utilities"
ai-utilities --help
```

Editable installs (`pip install -e .`) are not sufficient validation.

### 4.2 Optional dependencies

AI must not:

- Move optional dependencies into core requirements
- Import optional dependencies at module scope
- Hide missing-dependency errors

Missing extras must raise clear, actionable runtime errors, e.g.:

```
"The OpenAI provider requires the openai package.
Install with: pip install ai-utilities[openai]"
```

## 5. API Stability Rules

- Public APIs are stable within a major version
- No renaming, signature changes, or removals without explicit instruction
- Internal refactors must preserve behavior
- If behavior changes, tests must change first.

## 6. What AI Must NOT Do

AI must not:

- Add new dependencies without approval
- Rewrite large sections of code unless explicitly requested
- Introduce global flags, environment hacks, or magic defaults
- Silence errors instead of raising them
- "Fix" issues by weakening validation
- Mask failures to make tests pass

Passing tests by reducing coverage or assertions is a regression.

## 7. Required Validation Before Declaring "Done"

AI must explicitly verify and state that:

- All tests pass
- Packaging smoke checks pass
- Base install works without extras
- Optional providers fail clearly when dependencies are missing
- No fake or stub implementations were introduced

If any of these were skipped, AI must say so explicitly.

## 8. Authority

If there is a conflict between:

- README
- CONTRIBUTING
- CI configuration
- AI-generated suggestions

This document wins.

## 9. Communication & Style

### 9.1 No emojis in repository content

AI must not add emojis to any repository content, including:

- Source code (comments, docstrings, log messages)
- Tests and assertions
- Documentation (README, docs/*, changelogs)
- Commit messages, PR descriptions, or release notes generated as text

## Summary

This project values:

- Correctness over cleverness
- Explicit behavior over implicit magic
- Real execution over plausible code

AI assistance is welcome —
but only when it produces real, verifiable behavior.