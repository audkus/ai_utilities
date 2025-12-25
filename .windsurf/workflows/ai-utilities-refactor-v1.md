---
title: ai-utilities-refactor-v1
description: Refactor ai_utilities into a clean v1 library (src layout, no import side effects, tests)
---

1. Read the repository structure and identify current public API usage.
   - Output: brief list of entrypoints/functions other projects would import.

2. Create a new git branch `refactor/v1`.
   - Do not change functionality yet.

3. Convert to src layout:
   - Move package to `src/ai_utilities/`
   - Ensure imports are updated and minimal `__init__.py` exports stable API only.

4. Fix packaging:
   - Make `pyproject.toml` the source of truth (name/version/deps/optional deps).
   - Remove committed build artifacts (e.g., *.egg-info) and add to .gitignore.

5. Remove import-time side effects:
   - Ensure importing ai_utilities does not read/write config or initialize clients.
   - Configuration must be explicit (settings object or explicit load method).

6. Implement v1 API surface:
   - AiSettings (Pydantic)
   - AiClient with ask(), ask_many(), ask_json()
   - Keep provider adapter(s) behind an interface.

7. Add tests with pytest:
   - JSON extraction tests
   - Batch ordering test using a fake provider
   - “no side effects on import” test (import should not create files)

8. Run linters/tests and fix failures:
   - pytest
   - (optional) ruff/black/mypy if configured

9. Summarize changes and list any follow-ups (e.g., upgrade OpenAI adapter to Responses).
