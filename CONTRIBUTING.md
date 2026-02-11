# Contributing

## Scope of Contributions

We accept contributions that improve the library's core functionality, documentation, testing, and developer experience. Areas include:

- Bug fixes and stability improvements
- New provider integrations (following existing patterns)
- Documentation and examples
- Test coverage and reliability
- Performance optimizations
- Developer tooling and CI improvements

## Coding Standards

This project uses automated tooling to maintain code quality:

- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

### Setup

```bash
# Clone and install in development mode
git clone https://github.com/audkus/ai_utilities.git
cd ai_utilities
pip install -e ".[dev]"

# Run pre-commit setup
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_utilities --cov-report=html

# Run specific test file
pytest tests/unit/test_client.py

# Run with specific marker
pytest -m "unit"
```

### Code Quality

```bash
# Check linting
ruff check .

# Format code
ruff format .

# Type checking
mypy src/ai_utilities
```

## Pull Request Expectations

- **Clear description**: Explain what changes and why
- **Tests included**: New features should have test coverage
- **Documentation updated**: API changes require documentation updates
- **Passes CI**: All automated checks must pass
- **Single purpose**: One PR per feature or fix
- **Backwards compatible**: Avoid breaking changes unless necessary

## Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes with appropriate tests
4. Ensure all checks pass: `ruff check && mypy && pytest`
5. Submit pull request with clear description

## Release Process

Releases are managed by maintainers and follow semantic versioning. Contributors should focus on the main development branch unless specifically working on a release branch.

## Getting Help

- Check existing issues and documentation
- Create an issue for bugs or feature requests
- Use discussions for questions about contributions
