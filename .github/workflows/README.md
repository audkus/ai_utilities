# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, releases, and maintenance.

## Workflow Overview

### `ci.yml` - Main CI Pipeline
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Comprehensive testing and validation

**Jobs:**
- **test**: Multi-Python version testing (PRs: 3.9, 3.12 | Main: 3.9, 3.11, 3.12)
  - Lint with flake8
  - Type checking with mypy
  - Unit tests with pytest
  - Coverage reporting
- **minimal-install**: Minimal installation verification
- **integration-test**: Real-world testing on main branch (optional)
- **security-scan**: Vulnerability checking with safety and bandit (optional)
- **build-docs**: Documentation and example validation (optional)
- **compatibility-test**: Cross-platform testing (optional)
- **notify**: Success/failure reporting for required jobs

**Required vs Optional:**
- Required (blocks PRs): test, minimal-install
- Optional (informational): integration-test, security-scan, build-docs, compatibility-test

### `release.yml` - Release Pipeline
**Triggers**: Git tags (v*)  
**Purpose**: Automated PyPI releases

**Jobs:**
- **validate-version**: Version consistency check
- **test**: Final validation before release
- **build**: Package creation and validation
- **publish**: Upload to PyPI
- **create-release**: GitHub release creation
- **notify**: Release status reporting

**Requirements:**
- `PYPI_API_TOKEN` secret for PyPI upload

### `minimal-install.yml` - Minimal Install Verification
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Verify minimal install works without providers

**Jobs:**
- **minimal-install**: Core functionality testing
- **install-options**: Test all installation variants

### `provider-health.yml` - Provider Health Monitoring
**Triggers**: Scheduled (every 6 hours), Manual dispatch  
**Purpose**: Monitor external provider availability

**Jobs:**
- **provider-health-check**: Test provider APIs and generate reports

**Features:**
- Non-blocking observational monitoring
- Artifact-based reporting (reports not committed)
- Graceful handling of missing credentials

### `dependency-update.yml` - Dependency Management
**Triggers**: Weekly (Monday 9 AM UTC), Manual dispatch  
**Purpose**: Keep dependencies up to date

**Jobs:**
- **update-dependencies**: Updates requirements files and creates PR

### `benchmarks.yml` - Performance Benchmarks
**Triggers**: Daily schedule, Manual dispatch  
**Purpose**: Track performance over time

**Jobs:**
- **benchmark**: Run performance tests and generate reports

**Features:**
- Non-blocking observational monitoring
- Artifact-based reporting
- Optional dependency handling

## Key Features

### Testing Strategy
- **Required jobs**: Block PRs and ensure core functionality
- **Optional jobs**: Provide additional signal without blocking
- **Matrix optimization**: Faster PRs with reduced Python version scope
- **Cross-platform**: Linux, Windows, macOS testing (optional)

### Release Safety
- Version consistency validation (git tag vs pyproject.toml)
- Automated PyPI publishing
- GitHub release creation
- Comprehensive validation pipeline

### Observational Monitoring
- Provider health checks (scheduled, non-blocking)
- Performance benchmarks (isolated, optional)
- Dependency updates (automated PRs)
- All reports stored as artifacts, not committed

### Quality Assurance
- Type checking with mypy
- Code linting with flake8
- Security scanning with safety and bandit
- Documentation validation

## Setup Requirements

### Required Secrets
- `PYPI_API_TOKEN`: For publishing to PyPI

### Optional Secrets
- `CODECOV_TOKEN`: For coverage reporting (if using Codecov)

## Troubleshooting

### Common Issues

1. **Python version failures**: Check pyproject.toml for version compatibility
2. **Mypy failures**: Check type annotations and mypy configuration
3. **Security failures**: Review dependency updates and security advisories
4. **Integration failures**: Check external service availability and API keys

### Debugging Tips

- Use workflow logs to identify specific failure points
- Check artifact uploads for detailed reports (provider health, benchmarks)
- Use `workflow_dispatch` to manually trigger workflows for debugging
- Review dependency update PRs carefully before merging
- Remember: Optional jobs (integration, security, benchmarks) don't block releases

## Best Practices

1. **Local Testing**: Run `pytest` and `mypy` locally before pushing
2. **Incremental Changes**: Small PRs are easier to debug
3. **Dependency Updates**: Review dependency update PRs promptly
4. **Security**: Address security vulnerabilities quickly
5. **Monitoring**: Check observational workflows (provider health, benchmarks) for trends

## Workflow Status

Current status: All workflows implemented and tested

- Main CI pipeline (required + optional jobs)
- Release automation with version validation
- Dependency management
- Minimal install verification
- Provider health monitoring (observational)
- Performance benchmarks (observational)

Ready for production use!
