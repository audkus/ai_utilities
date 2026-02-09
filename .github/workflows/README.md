# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, releases, and maintenance.

## 🚨 CRITICAL: Blocking vs Non-Blocking Workflows

### 🔴 BLOCKING Workflows (Must Pass for Release)
These workflows **MUST** pass for any release. They block PRs and releases:

- **`ci.yml`** - Main CI pipeline (core testing)
- **`test_suite.yml`** - Comprehensive test suite
- **`minimal-install.yml`** - Minimal installation verification

### 🟡 NON-BLOCKING Workflows (Informational Only)
These workflows **DO NOT** block releases. They provide additional signal and monitoring:

- **`benchmarks.yml`** - Performance monitoring
- **`provider-health.yml`** - External provider monitoring
- **`dependency-update.yml`** - Dependency management
- **`release.yml`** - Release automation (only runs after blocking workflows pass)

## 🎯 Why This Approach?

### ✅ Benefits of Blocking/Non-Blocking Separation

#### **🚀 Faster Development Cycle**
- **PRs aren't blocked** by non-critical issues
- **Contributors stay motivated** with quick feedback
- **False negatives reduced** - only core issues block

#### **🛡️ Release Safety Maintained**
- **Core functionality tested** by blocking workflows
- **Quality gates preserved** where they matter most
- **Release automation** still comprehensive

#### **📊 Better Signal Management**
- **Observational workflows** provide insights without friction
- **Performance monitoring** continues without blocking development
- **Provider health** tracked independently

#### **👥 Contributor Experience**
- **Less intimidating** contribution process
- **Clear expectations** about what blocks vs what doesn't
- **Faster onboarding** for new contributors

### ⚠️ Risk Mitigation

#### **✅ What We Protect**
- **Core functionality** - Blocking workflows ensure main features work
- **Installation integrity** - Minimal install verification
- **Test coverage** - Comprehensive test suite validation

#### **🟡 What We Accept**
- **Performance variations** - Benchmarks provide trends, not gates
- **External service issues** - Provider health is informational
- **Dependency timing** - Updates can be reviewed and merged when ready

## 📋 Workflow Overview

### `ci.yml` - Main CI Pipeline 🔴 **BLOCKING**
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Comprehensive testing and validation
**Status**: **MUST PASS** for PRs and releases

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

### `test_suite.yml` - Comprehensive Test Suite 🔴 **BLOCKING**
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Extended testing beyond core CI
**Status**: **MUST PASS** for PRs and releases

**Jobs:**
- **extended-tests**: Comprehensive test coverage
- **integration-tests**: Real-world scenario testing
- **performance-tests**: Performance regression testing

### `minimal-install.yml` - Minimal Install Verification 🔴 **BLOCKING**
**Triggers**: Push to main/develop, Pull Requests  
**Purpose**: Verify minimal install works without providers
**Status**: **MUST PASS** for PRs and releases

**Jobs:**
- **minimal-install**: Core functionality testing
- **install-options**: Test all installation variants

### `release.yml` - Release Pipeline 🟡 **NON-BLOCKING**
**Triggers**: Git tags (v*)  
**Purpose**: Automated PyPI releases
**Status**: Runs after blocking workflows pass

**Jobs:**
- **validate-version**: Version consistency check
- **test**: Final validation before release
- **build**: Package creation and validation
- **publish**: Upload to PyPI
- **create-release**: GitHub release creation
- **notify**: Release status reporting

**Requirements:**
- `PYPI_API_TOKEN` secret for PyPI upload

### `provider-health.yml` - Provider Health Monitoring 🟡 **NON-BLOCKING**
**Triggers**: Scheduled (every 6 hours), Manual dispatch  
**Purpose**: Monitor external provider availability
**Status**: Informational only, does not block releases

**Jobs:**
- **provider-health-check**: Test provider APIs and generate reports

**Features:**
- Non-blocking observational monitoring
- Artifact-based reporting (reports not committed)
- Graceful handling of missing credentials

### `dependency-update.yml` - Dependency Management 🟡 **NON-BLOCKING**
**Triggers**: Weekly (Monday 9 AM UTC), Manual dispatch  
**Purpose**: Keep dependencies up to date
**Status**: Creates PRs for review, does not block

**Jobs:**
- **update-dependencies**: Updates requirements files and creates PR

### `benchmarks.yml` - Performance Benchmarks 🟡 **NON-BLOCKING**
**Triggers**: Daily schedule, Manual dispatch  
**Purpose**: Track performance over time
**Status**: Observational monitoring only

**Jobs:**
- **benchmark**: Run performance tests and generate reports

**Features:**
- Non-blocking observational monitoring
- Artifact-based reporting
- Optional dependency handling

## Key Features

### 🚨 Blocking vs Non-Blocking Strategy

#### **🔴 Blocking Workflows (Release Critical)**
- **Core functionality validation** - Ensures main features work
- **Installation integrity** - Verifies package installs correctly
- **Test coverage** - Comprehensive test suite validation
- **Required for PRs** - Block merges if they fail
- **Required for releases** - Must pass before deployment

#### **🟡 Non-Blocking Workflows (Observational)**
- **Performance monitoring** - Track trends without blocking
- **Provider health** - External service monitoring
- **Dependency management** - Automated updates via PRs
- **Release automation** - Runs after blocking workflows pass
- **Informational only** - Provide insights, not gates

### Testing Strategy
- **Required jobs**: Block PRs and ensure core functionality
- **Optional jobs**: Provide additional signal without blocking
- **Matrix optimization**: Faster PRs with reduced Python version scope
- **Cross-platform**: Linux, Windows, macOS testing (optional)

### Release Safety
- **Multi-layer validation**: Blocking workflows ensure quality
- **Version consistency**: Automated checks before release
- **Comprehensive testing**: Full validation pipeline
- **Observational monitoring**: Continuous insights without friction

### Observational Monitoring
- **Provider health checks**: Scheduled, non-blocking monitoring
- **Performance benchmarks**: Isolated, optional tracking
- **Dependency updates**: Automated PRs for review
- **Artifact-based reporting**: All reports stored as artifacts, not committed

### Quality Assurance
- **Type checking**: mypy validation in blocking workflows
- **Code linting**: flake8 validation in blocking workflows
- **Security scanning**: Optional safety and bandit checks
- **Documentation validation**: Optional docs and examples testing

## Setup Requirements

### Required Secrets
- `PYPI_API_TOKEN`: For publishing to PyPI

### Optional Secrets
- `CODECOV_TOKEN`: For coverage reporting (if using Codecov)

## Troubleshooting

### Common Issues

1. **Blocking workflow failures** (🔴 ci.yml, test_suite.yml, minimal-install.yml)
   - **Impact**: Blocks PRs and releases
   - **Action**: Must be fixed immediately
   - **Check**: Core functionality, installation, test coverage

2. **Non-blocking workflow failures** (🟡 benchmarks.yml, provider-health.yml, dependency-update.yml)
   - **Impact**: Informational only, does not block releases
   - **Action**: Review when convenient, create PR for fixes
   - **Check**: Performance trends, external services, dependency updates

3. **Python version failures**: Check pyproject.toml for version compatibility
4. **Mypy failures**: Check type annotations and mypy configuration
5. **Security failures**: Review dependency updates and security advisories
6. **Integration failures**: Check external service availability and API keys

### Debugging Tips

- **Use workflow logs** to identify specific failure points
- **Check artifact uploads** for detailed reports (provider health, benchmarks)
- **Use `workflow_dispatch`** to manually trigger workflows for debugging
- **Review dependency update PRs** carefully before merging
- **Remember**: Non-blocking jobs (integration, security, benchmarks) don't block releases
- **Focus on blocking workflows** first for critical issues

### Workflow Status Quick Reference

| Workflow | Status | Action Required |
|----------|--------|-----------------|
| 🔴 ci.yml | **BLOCKING** | Fix immediately |
| 🔴 test_suite.yml | **BLOCKING** | Fix immediately |
| 🔴 minimal-install.yml | **BLOCKING** | Fix immediately |
| 🟡 release.yml | **NON-BLOCKING** | Review after blocking pass |
| 🟡 benchmarks.yml | **NON-BLOCKING** | Review when convenient |
| 🟡 provider-health.yml | **NON-BLOCKING** | Monitor trends |
| 🟡 dependency-update.yml | **NON-BLOCKING** | Review PRs when ready |

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
