# Coverage Workflow

## How to Run Tests

```bash
# Run all tests (default, unit tests only)
pytest -q

# Run specific test categories
pytest tests/unit/           # Fast, deterministic tests
pytest tests/integration/   # External dependencies, gated
pytest tests/policies/      # Project rules and hygiene
pytest tests/regression/    # Bug fixes and coverage issues
pytest tests/coverage_guards/  # Import path and artifact guards
```

## How to Run Coverage (Canonical)

```bash
# Run coverage with correct timing (starts before imports)
python -m coverage run -m pytest

# Generate all reports
python -m coverage report
python -m coverage xml -o coverage_reports/coverage.xml
python -m coverage html -d coverage_reports/html

# Or use tox
tox -e coverage
```

## Why We Use `python -m coverage run -m pytest`

Coverage must start **before** pytest imports any modules. If coverage starts after imports (like with pytest-cov), it misses the initial import execution and shows misleading results like "module was never imported".

The canonical command ensures:
- Coverage starts before all imports
- All code execution is tracked
- Import-path issues are detected by guards
- Reports are generated in the correct location

## Coverage Rules

- **Normal pytest**: Never creates coverage artifacts
- **Coverage artifacts**: Only in `coverage_reports/` directory
- **Import path guard**: Ensures tests import from `src/`, not site-packages
- **Examples**: Never executed or collected by pytest

## Coverage Reports Location

All coverage artifacts are generated in `coverage_reports/`:
- `coverage_reports/coverage.xml` - Machine-readable report
- `coverage_reports/html/index.html` - Human-readable HTML report

No coverage files are created in the repository root during normal operation.
