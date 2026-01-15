# Test Isolation Issues - Analysis and Triage

## Problem Summary

The test suite exhibits order-dependent failures caused by global state pollution. Tests that run individually pass, but fail when run in full suites due to leaked environment state.

## Top Failing Tests Categories

### 1. Environment Variable Pollution
**Affected Tests**: 
- `test_env_overrides.py::TestEnvOverrides::test_ai_settings_integration_behavior`
- `test_env_overrides.py::TestEnvOverrides::test_override_only_baseline`
- `test_env_overrides.py::TestEnvOverrides::test_task_inheritance_no_crosstalk`
- `test_env_overrides.py::TestEnvOverrides::test_ai_settings_integration`
- `test_env_overrides.py::TestEnvOverrides::test_ai_settings_precedence`
- `test_env_overrides.py::TestEnvOverrides::test_async_isolation`
- `test_env_overrides.py::TestEnvOverrides::test_thread_isolation`

**Root Cause**: Tests modify `os.environ['AI_MODEL']` and other environment variables without proper cleanup, causing subsequent tests to read polluted values.

**Evidence**: Tests expect default model 'test-model-1' but get 'gpt-3.5-turbo' or values from previous tests.

### 2. Contextvar Contamination
**Affected Tests**: Same as above - all env_overrides tests

**Root Cause**: The `override_env()` context manager uses contextvars but the state may not be properly isolated between test runs, especially in async/thread contexts.

**Source**: `ai_utilities/env_overrides.py` contextvar implementation

### 3. Module Cache/Import Persistence
**Affected Tests**: 
- `test_api_key_resolver.py::TestIntegrationWithClient::test_create_client_with_explicit_key`
- `test_api_key_resolver.py::TestIntegrationWithClient::test_create_client_without_key_raises_error`
- `test_api_key_resolver.py::TestIntegrationWithClient::test_create_client_with_env_file`

**Root Cause**: `AiSettings` and related configuration classes cache environment state at import time or during first instantiation, leading to stale data in subsequent tests.

**Source**: `ai_utilities/config_models.py` model validators and `pydantic-settings` behavior

## Suspected Pollution Sources

### Primary Sources:
1. **`os.environ` direct mutation** - Tests directly set/unset environment variables
2. **`AiSettings` model validators** - Cache environment state during validation
3. **`pydantic-settings` BaseSettings** - Reads environment at class instantiation
4. **Contextvar state** - May persist across test boundaries
5. **Module-level imports** - Configuration modules may cache state at import

### Secondary Sources:
1. **Singleton patterns** - Any global singletons in the codebase
2. **Background threads/tasks** - May maintain state across tests
3. **File system state** - Temporary files or caches not cleaned up

## Order Dependence Demonstration

Created `test_order_dependence.py` which proves:
- First test sets `AI_MODEL='test-model-from-first-test'`
- Second test expects clean environment but gets polluted value
- Override contexts also fail due to underlying environment pollution

## Impact Assessment

- **Test Reliability**: Tests are non-deterministic based on execution order
- **CI/CD**: Parallel test execution would be unreliable
- **Development**: Local testing experience is inconsistent
- **Coverage**: Some code paths may not be properly tested due to test failures

## Next Steps for Phase 2

1. **Environment Snapshot/Restore**: Implement pytest fixtures to capture and restore `os.environ`
2. **Contextvar Reset**: Explicitly reset contextvars to known defaults
3. **Module Cache Reset**: Implement `reset_global_state_for_tests()` function
4. **Test Migration**: Update tests to use proper isolation mechanisms

## Technical Debt

This issue indicates architectural problems:
- Heavy reliance on global environment state
- Lack of dependency injection for configuration
- Insufficient test isolation boundaries
- Mixed concerns between configuration and test setup
