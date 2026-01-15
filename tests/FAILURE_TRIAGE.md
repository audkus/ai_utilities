# Test Failure Triage

## Current Snapshot
- **Total Tests**: 1,981
- **Failed**: 460 
- **Errors**: 16
- **Passed**: 1,521
- **Skipped**: 54
- **Coverage**: 78% (hanging issue fixed)

## Failure Inventory

### High Priority Failures (>10 each)

| Test File | Count | Error Type | Bucket | Owner |
|-----------|-------|------------|--------|-------|
| test_client_core.py | 29 | AssertionError/TypeError | Core Regression | client |
| test_main_script.py | 27 | AssertionError/TypeError | Core Regression | cli |
| test_webui_api_helper.py | 20 | ImportError | Broken Imports | webui |
| test_daily_provider_check.py | 20 | AssertionError | Integration | providers |
| test_provider_change_detector.py | 19 | AssertionError | Integration | providers |
| test_provider_diagnostic.py | 18 | AssertionError | Integration | providers |
| test_performance_benchmarks.py | 18 | AssertionError | Integration | providers |
| test_openai_client.py | 17 | ImportError/AssertionError | Broken Imports | client |
| test_env_detection.py | 14 | AssertionError | Environment Config | settings |
| test_ask_typed.py | 14 | AssertionError | Core Regression | client |

### Error Types Identified

1. **ImportError**: Missing classes like `OpenAIClient`, `WebUIAPIHelper`
2. **AssertionError**: Behavior mismatches in core functionality
3. **TypeError**: Function signature changes
4. **ValidationError**: Pydantic model validation changes
5. **AttributeError**: Missing module attributes

### Initial Bucket Classification

- **Bucket A (Broken Imports)**: ~50 failures
- **Bucket B (Deprecated/Removed APIs)**: ~30 failures  
- **Bucket C (Environment/Config)**: ~40 failures
- **Bucket D (True Regressions)**: ~100 failures
- **Bucket E (Integration)**: ~240 failures

---

## Phase 1 — Current Contract Analysis

### Public API Exports (from __init__.py)

**🚀 STABLE PUBLIC API (v1.x) - Guaranteed stable:**
- `AiClient`, `AsyncAiClient`, `AiSettings`, `create_client`
- `AskResult`, `UploadedFile`
- `JsonParseError`, `parse_json_from_text`
- `AudioProcessor`, `load_audio_file`, `save_audio_file`, `validate_audio_file`, `get_audio_info`
- `UsageTracker`, `create_usage_tracker`

**📦 COMPATIBILITY EXPORTS (Available but may change):**
- Providers: `BaseProvider`, `OpenAIProvider`, `OpenAICompatibleProvider`, `create_provider`
- Rate limiting: `RateLimitFetcher`, `RateLimitInfo`
- Token counting: `TokenCounter`
- Audio models: `AudioFormat`, `TranscriptionRequest`, etc.
- Usage tracking: `ThreadSafeUsageTracker`, `UsageScope`, `UsageStats`

### Supported Classes/Functions

**Core Client:**
- `AiClient(settings: Optional[AiSettings] = None)` - Main client
- `AsyncAiClient(settings: Optional[AiSettings] = None)` - Async version
- `AiSettings` - Configuration model (pydantic-based)
- `create_client(**kwargs)` - Factory function

**Key Methods:**
- `client.ask(prompt: str) -> AskResult`
- `client.ask_json(prompt: str) -> dict`
- `client.transcribe_audio(file_path: str) -> dict`
- `client.generate_audio(text: str, voice: str) -> bytes`

**Provider System:**
- Uses `create_provider()` factory
- `OpenAIProvider` is lazy-loaded (requires `ai-utilities[openai]`)
- `OpenAICompatibleProvider` for compatible APIs

### Deprecated/Removed Items

**Confirmed Removed:**
- `OpenAIClient` class (replaced by `OpenAIProvider` + `AiClient`)
- `WebUIAPIHelper` class (removed from codebase)
- Direct rate_limit_fetcher module access (now via class)

**Architecture Changes:**
- No import-time side effects
- Lazy loading of optional dependencies
- Provider-based architecture instead of direct clients

### v1.0.0b1 Required Behavior

**Core Requirements:**
1. **AiClient** must work with environment variables or explicit settings
2. **Configuration precedence**: request params > AiSettings > environment > defaults
3. **Error handling**: proper exceptions for missing API keys, invalid models
4. **Audio processing**: transcribe and generate audio must work
5. **Usage tracking**: optional but functional when enabled
6. **Provider isolation**: different providers should not interfere

**Critical Paths:**
- `AiClient().ask("test")` should work with OPENAI_API_KEY env var
- `AiClient(AiSettings(api_key="key", model="gpt-4")).ask()` should work
- Missing API key should raise `ProviderConfigurationError`
- Invalid model should raise appropriate validation error

---

## Phase 2 — Detailed Bucketing

### Bucket A — Broken Imports (50+ failures)

| Test File | Count | Error Type | Missing Symbol | Status |
|-----------|-------|------------|----------------|---------|
| test_webui_api_helper.py | 20 | ImportError | `WebUIAPIHelper` | **REMOVED** - Class doesn't exist |
| test_rate_limit_fetcher.py | 13 | AttributeError | `OpenAIClient` | **REMOVED** - Use `OpenAIProvider` instead |
| test_usage_tracking.py | 14 | TypeError | `auto_setup` param | **DEPRECATED** - Parameter removed |

**Action**: Remove or rewrite these tests to use current API.

### Bucket B — Deprecated/Removed APIs (30+ failures)

| Test File | Count | Issue | Replacement |
|-----------|-------|-------|-------------|
| test_main_script.py | 27 | Old CLI interface | Use new `ai-utilities setup` |
| test_advanced_caching.py | 10 | Old cache API | Use new `CacheBackend` |
| test_ai_settings_model_field.py | 12 | Old validation | Use new `AiSettings` |

**Action**: Delete tests for removed features, write new tests for current behavior.

### Bucket C — Environment/Config Issues (40+ failures)

| Test File | Count | Issue | Fix Strategy |
|-----------|-------|-------|--------------|
| test_env_detection.py | 14 | CI environment detection | Use monkeypatch isolation |
| test_settings_precedence.py | 12 | Env var loading | Mock environment |
| test_config_models.py | 14 | Pydantic validation | Update validation rules |

**Action**: Add proper environment isolation fixtures.

### Bucket D — True Regressions (100+ failures)

| Test File | Count | Issue | Priority |
|-----------|-------|-------|----------|
| test_client_core.py | 29 | Unicode handling, function signatures | **HIGH** |
| test_ask_typed.py | 14 | Typed response validation | **HIGH** |
| test_client_comprehensive.py | 13 | Client behavior changes | **HIGH** |

**Action**: Fix code to match documented contract.

### Bucket E — Integration Tests (240+ failures)

| Test File | Count | Issue | Action |
|-----------|-------|-------|--------|
| test_provider_change_detector.py | 19 | Network calls | Mock HTTP layer |
| test_provider_diagnostic.py | 18 | External services | Mark as integration |
| test_daily_provider_check.py | 20 | Provider monitoring | Mock or mark |
| test_performance_benchmarks.py | 18 | Performance tests | Separate suite |

**Action**: Mock external dependencies or mark as integration tests.

---

### Verified Symbol Status

**Confirmed Removed:**
- `WebUIAPIHelper` - Not found in any source file
- `OpenAIClient` - Use `OpenAIProvider` + `AiClient` instead
- `auto_setup` parameter - Removed from usage tracking

**Confirmed Renamed/Moved:**
- Rate limiting access patterns changed
- Cache system restructured
- CLI interface redesigned

**Architecture Changes:**
- Provider-based architecture
- Lazy loading of optional dependencies
- No import-time side effects

---

## Phase 3 — Fix Order
1. Core client tests: test_client_core.py, test_openai_client.py, test_main_script.py
2. Settings/config precedence + env detection tests  
3. Provider diagnostics/detectors (non-network)
4. Integration tests (mock or mark)

---

## Phase 4 — Actions Per Bucket
[TO BE COMPLETED]

---

## Phase 5 — Execution Plan
[TO BE COMPLETED]

---

## Phase 6 — Definition of Done
- ✅ pytest -q passes
- ✅ pytest --cov=src --cov-report=term-missing passes
- ✅ All core functionality tests pass
- ✅ Integration tests properly marked/mocked
