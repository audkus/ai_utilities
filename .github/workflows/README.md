# 🔄 CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, releases, and maintenance.

## 📋 Workflow Overview

### 🚀 `ci.yml` - Main CI Pipeline
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Comprehensive testing and validation

**Jobs:**
- **test**: Multi-Python version testing (3.9, 3.10, 3.11)
  - Lint with flake8
  - Type checking with mypy
  - Unit tests with pytest
  - Coverage reporting
- **integration-test**: Real-world testing on main branch
- **security-scan**: Vulnerability checking with safety and bandit
- **build-docs**: Documentation and example validation
- **performance-test**: Import and creation speed benchmarks
- **compatibility-test**: Cross-platform testing (Linux, Windows, macOS)
- **notify**: Success/failure reporting

### 📦 `release.yml` - Release Pipeline
**Triggers**: Git tags (v*)  
**Purpose**: Automated PyPI releases

**Jobs:**
- **test**: Final validation before release
- **build**: Package creation and validation
- **create-release**: GitHub release creation
- **notify**: Release status reporting

**Requirements:**
- `PYPI_API_TOKEN` secret for PyPI upload

### 🔧 `dependency-update.yml` - Dependency Management
**Triggers**: Weekly (Monday 9 AM UTC), Manual dispatch  
**Purpose**: Keep dependencies up to date

**Jobs:**
- **update-dependencies**: Updates requirements files and creates PR

**Features:**
- Automatic dependency updates
- Testing before PR creation
- Clean PR with detailed description

### ✅ `minimal-install.yml` - Minimal Install Verification
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Verify minimal install works without providers

**Jobs:**
- **minimal-install**: Core functionality testing
- **install-options**: Test all installation variants

### 🏥 `provider-health.yml` - Provider Health Monitoring
**Triggers**: Scheduled (daily), Manual dispatch  
**Purpose**: Monitor external provider availability

**Jobs:**
- **health-check**: Test provider connectivity and response times

## 🎯 Key Features

### 🔍 Comprehensive Testing
- **Multi-version**: Python 3.9, 3.10, 3.11
- **Cross-platform**: Linux, Windows, macOS
- **Type safety**: Full mypy validation
- **Security**: Vulnerability scanning
- **Performance**: Speed benchmarks

### 📊 Quality Gates
- All tests must pass
- Type checking must pass
- Security scan must pass
- Performance benchmarks must meet thresholds

### 🚀 Automated Releases
- Tag-based releases
- PyPI publishing
- GitHub releases
- Dependency updates

### 📈 Monitoring
- Provider health checks
- Performance tracking
- Security vulnerability monitoring
- Dependency freshness

## 🔧 Setup Requirements

### Required Secrets
- `PYPI_API_TOKEN`: For publishing to PyPI

### Optional Secrets
- `CODECOV_TOKEN`: For coverage reporting (if using Codecov)

## 🚨 Troubleshooting

### Common Issues

1. **Python version failures**: Check pyproject.toml for version compatibility
2. **Mypy failures**: Check type annotations and mypy configuration
3. **Security failures**: Review dependency updates and security advisories
4. **Performance failures**: Check for performance regressions in imports/creation

### Debugging Tips

- Use workflow logs to identify specific failure points
- Check artifact uploads for detailed reports
- Use `workflow_dispatch` to manually trigger workflows for debugging
- Review dependency update PRs carefully before merging

## 📝 Best Practices

1. **Local Testing**: Run `pytest` and `mypy` locally before pushing
2. **Incremental Changes**: Small PRs are easier to debug
3. **Dependency Updates**: Review dependency update PRs promptly
4. **Performance**: Monitor performance benchmarks for regressions
5. **Security**: Address security vulnerabilities quickly

## 🔄 Workflow Status

Current status: ✅ All workflows implemented and tested

- ✅ Main CI pipeline
- ✅ Release automation
- ✅ Dependency management
- ✅ Minimal install verification
- ✅ Provider health monitoring

Ready for production use! 🚀
