# Contributing to AI Utilities

Thank you for your interest in contributing to AI Utilities! This document provides guidelines for contributors.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/ai_utilities.git
   cd ai_utilities
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or: .venv\Scripts\activate  # Windows
   ```

3. **Install in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

## Code Quality Standards

### Before Committing
Run this command to ensure code quality:
```bash
ruff check . --fix && ruff format . && mypy src/ && pytest
```

### Individual Tools
- **Linting:** `ruff check . --fix`
- **Formatting:** `ruff format .`
- **Type checking:** `mypy src/`
- **Testing:** `pytest`

## Testing

### Running Tests
```bash
pytest                    # All tests
pytest -m "not slow"     # Skip slow tests
pytest -v                # Verbose output
pytest --cov=src         # With coverage
```

### Test Structure
- Unit tests: `tests/test_*.py`
- Integration tests: `tests/integration/`
- Provider tests: `tests/provider_monitoring/`

## Adding New Providers

1. **Create provider class** in `src/ai_utilities/providers/`
2. **Add to factory** in `src/ai_utilities/providers/provider_factory.py`
3. **Add to monitoring** in `scripts/provider_health_monitor.py`
4. **Write tests** in `tests/provider_monitoring/`
5. **Update documentation** in `docs/all-providers-guide.md`

## Documentation

### README Changes
- Keep it concise and focused on user-facing information
- Move detailed content to `docs/` folder
- Ensure all code examples work

### Documentation in docs/
- Use clear, descriptive filenames
- Update `docs/README.md` index when adding new pages
- Follow existing markdown formatting

## Submitting Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test thoroughly**

3. **Commit with clear messages:**
   ```bash
   git commit -m "feat: add new provider support"
   ```

4. **Push and create pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- **Title:** Use conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
- **Description:** Explain what you changed and why
- **Tests:** Ensure all tests pass
- **Documentation:** Update relevant docs
- **Breaking Changes:** Clearly label and provide migration guidance

## Code Style

- **Python:** Follow PEP 8
- **Type hints:** Required for all public functions
- **Docstrings:** Google-style for public functions/classes
- **Imports:** Grouped (stdlib, third-party, local)

## Reporting Issues

- **Bug reports:** Include reproduction steps, environment info
- **Feature requests:** Describe use case and proposed solution
- **Questions:** Use GitHub Discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
