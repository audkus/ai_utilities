# Release Checklist

This checklist describes the manual testing process for AI Utilities releases.

## Overview

The manual testing process consists of two tiers:

### Tier 1 Tests (All Providers, No Network)
- **Purpose:** Validate provider configuration and error handling
- **Scope:** All supported providers
- **Requirements:** No API keys, no network access
- **Environment:** Isolated virtual environment with minimal install

### Tier 2 Tests (OpenAI Only, Real Calls)
- **Purpose:** End-to-end testing with actual API calls
- **Scope:** OpenAI provider only (default)
- **Requirements:** Valid `AI_API_KEY` environment variable
- **Environment:** Same isolated environment with network access

## Pre-Release Commands

### 1. Environment Setup
```bash
# Ensure clean working tree
git status

# Create release branch (if not already on it)
git checkout release/1.0.0b1-manual-tests-openai
```

### 2. Run Tier 1 Tests
```bash
# Run all Tier 1 tests (no network required)
./manual_tests/run_manual_tests.sh

# Expected outcome: All providers should show PASS or SKIP
# FAIL indicates a bug that must be fixed before release
```

### 3. Run Tier 2 Tests (Optional for verification)
```bash
# Set your OpenAI API key
export AI_API_KEY="your-openai-api-key-here"

# Run Tier 1 + Tier 2 tests
./manual_tests/run_manual_tests.sh --tier2

# Expected outcome: Tier 1 all green, Tier 2 Openai PASS
```

### 4. Review Results
```bash
# View the generated report
cat reports/manual_report_*.md
```

## Result Interpretation

### PASS
- **Tier 1:** Provider configuration works correctly
- **Tier 2:** End-to-end functionality verified

### SKIP
- **Tier 1:** Optional dependencies missing (acceptable)
- **Tier 2:** API key not configured (acceptable for testing)

### FAIL
- **Tier 1:** Bug in provider configuration or error handling
- **Tier 2:** API call failed or timeout (investigate required)

## Required Environment Variables

### For Tier 2 Testing Only
```bash
# Required for OpenAI Tier 2 tests
export AI_API_KEY="sk-your-openai-api-key"

# Optional: Override provider (not recommended for standard release)
export AI_PROVIDER="openai"
```

## Pre-Release Decision Rules

### v1.0.0b1 → Final Release Criteria
1. **Tier 1:** All providers must be PASS or SKIP
   - Zero FAIL results allowed
   - SKIP only acceptable for missing optional dependencies

2. **Tier 2:** OpenAI must be PASS when API key is configured
   - Required for user-facing functionality verification
   - Can be skipped if API key unavailable, but should be verified before final release

3. **Unit Tests:** All pytest tests must pass
   ```bash
   pytest tests/ -q
   ```

4. **Working Tree:** Must be clean (no uncommitted changes)
   ```bash
   git status
   ```

## Troubleshooting

### Common Issues

#### Tier 1 FAIL Results
- **Missing imports:** Check provider factory implementation
- **Configuration errors:** Verify AiSettings and provider creation logic
- **Dependency issues:** Ensure minimal install works correctly

#### Tier 2 FAIL Results
- **API key issues:** Verify key format and permissions
- **Network timeouts:** Check internet connectivity and API status
- **Rate limiting:** Wait and retry, or check API quotas

#### Environment Issues
- **Virtual environment:** Ensure clean venv creation
- **Package installation:** Verify minimal install works
- **Path issues:** Check script directory structure

### Debug Mode
```bash
# Run with verbose output
bash -x ./manual_tests/run_manual_tests.sh

# Run with extended timeout
./manual_tests/run_manual_tests.sh --timeout 120
```

## Release Process

### Before Release
1. Run complete manual test suite
2. Review all generated reports
3. Verify unit tests pass
4. Check documentation is up to date

### Release Day
1. Tag the release:
   ```bash
   git tag -a v1.0.0b1 -m "Release v1.0.0b1"
   git push origin v1.0.0b1
   ```

2. Create release notes
3. Update documentation if needed

### Post-Release
1. Monitor for issues
2. Collect user feedback
3. Plan next release cycle

## Automation Notes

- **Manual tests are intentionally NOT automated**
- **No network calls in CI/CD pipelines**
- **Manual tests are opt-in only**
- **All outputs are gitignored**

This ensures manual testing remains reliable and doesn't interfere with automated processes.

## Support

For issues with the manual testing process:

1. Check this checklist first
2. Review generated reports for specific error messages
3. Check GitHub Issues for known problems
4. Create new issue with detailed error information

---

*This checklist is part of the AI Utilities release process and should be followed for all releases.*
