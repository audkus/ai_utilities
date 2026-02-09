# Testing Plan - V1 Beta "Rock Solid"

## Goal

Raise test coverage from ~15% to comprehensive coverage by exercising README-promised features with deterministic, offline tests that execute real code paths.

## Non-Negotiable Rules

- Use pytest only
- No external network calls (mock provider SDKs at boundary only)
- Execute our own request-building, config-resolution, caching, CLI/setup logic
- Tests must be deterministic across machines
- Use monkeypatch for env vars, never rely on developer environment
- Prefer small focused unit tests + thin integration slice
- Avoid production code changes unless minimal testability hook is required

## Feature → Test Mapping

### README Promised Features

| README Feature | Test Module | Phase | Status |
|----------------|-------------|-------|---------|
| **Core Client** | | | |
| `AiClient.ask()` basic usage | `test_client.py` | Phase 1 | ✅ IMPLEMENTED |
| Per-request overrides (model, temp, tokens) | `test_client.py` | Phase 1 | ✅ IMPLEMENTED |
| Error handling & provider exceptions | `test_client.py` | Phase 1 | ✅ IMPLEMENTED |
| List prompts handling | `test_client.py` | Phase 1 | ✅ IMPLEMENTED |
| **Configuration** | | | |
| Environment variable loading | `test_settings.py` | Phase 1 | ✅ IMPLEMENTED |
| .env file support | `test_settings.py` | Phase 1 | ✅ IMPLEMENTED |
| Config precedence order | `test_settings.py` | Phase 1 | ✅ IMPLEMENTED |
| Missing required config errors | `test_settings.py` | Phase 1 | ✅ IMPLEMENTED |
| **Provider Management** | | | |
| Provider factory selection | `test_providers.py` | Phase 1 | ✅ IMPLEMENTED |
| Unknown provider errors | `test_providers.py` | Phase 1 | ✅ IMPLEMENTED |
| OpenAI-compatible provider path | `test_providers.py` | Phase 1 | ✅ IMPLEMENTED |
| **Caching** | | | |
| Intelligent caching with namespaces | `test_caching.py` | Phase 2 | 📋 PLANNED |
| Memory cache backend | `test_caching.py` | Phase 2 | 📋 PLANNED |
| SQLite cache backend | `test_caching.py` | Phase 2 | 📋 PLANNED |
| Cache invalidation and TTL | `test_caching.py` | Phase 2 | 📋 PLANNED |
| **Async Operations** | | | |
| AsyncAiClient basic usage | `test_async_client.py` | Phase 3 | 📋 PLANNED |
| Async error handling | `test_async_client.py` | Phase 3 | 📋 PLANNED |
| Async caching behavior | `test_async_client.py` | Phase 3 | 📋 PLANNED |
| **CLI & Setup** | | | |
| `ai-utilities setup` wizard flows | `test_cli.py` | Phase 4 | 📋 PLANNED |
| Non-interactive setup mode | `test_cli.py` | Phase 4 | 📋 PLANNED |
| Setup wizard error handling | `test_cli.py` | Phase 4 | 📋 PLANNED |
| **Audio Processing** | | | |
| Audio transcription path | `test_audio.py` | Phase 5 | 📋 PLANNED |
| Audio generation path | `test_audio.py` | Phase 5 | 📋 PLANNED |
| Audio error handling | `test_audio.py` | Phase 5 | 📋 PLANNED |
| **Rate Limiting** | | | |
| Rate limit enforcement | `test_rate_limiting.py` | Phase 6 | 📋 PLANNED |
| Deterministic time control | `test_rate_limiting.py` | Phase 6 | 📋 PLANNED |
| Rate limit recovery | `test_rate_limiting.py` | Phase 6 | 📋 PLANNED |

## Phase Details

### Phase 1: Core Functionality ✅ IMPLEMENTED

**Focus**: Core client, configuration, and provider selection

**Files to enhance**:
- `tests/test_client.py` - Core AiClient.ask() functionality
- `tests/test_settings.py` - AiSettings and config resolution  
- `tests/test_providers.py` - Provider factory and selection
- `tests/conftest.py` - Reusable fixtures

**Coverage targets**:
- `client.py`: 80%+ (currently ~11%)
- `config_models.py`: 70%+ (currently ~33%)
- `providers/__init__.py`: 90%+ (currently ~59%)
- `providers/base_provider.py`: 80%+ (currently ~65%)

### Phase 2: Caching 📋 PLANNED

**Focus**: Memory and SQLite caching backends with namespace behavior

**Files to create/enhance**:
- `tests/test_caching.py` - Comprehensive caching tests
- `tests/fake_provider.py` - Add caching-aware fake provider

**Coverage targets**:
- `cache/memory_cache.py`: 90%+
- `cache/sqlite_cache.py`: 90%+
- Client caching integration: 80%+

### Phase 3: Async Client 📋 PLANNED

**Focus**: AsyncAiClient functionality and async-specific behavior

**Files to create/enhance**:
- `tests/test_async_client.py` - Async client tests
- `tests/fake_provider.py` - Add FakeAsyncProvider

**Coverage targets**:
- `async_client.py`: 80%+
- Async provider integration: 80%+

### Phase 4: CLI & Setup Wizard 📋 PLANNED

**Focus**: Command-line interface and setup wizard flows

**Files to create/enhance**:
- `tests/test_cli.py` - CLI command tests
- `tests/test_setup_wizard.py` - Setup wizard tests

**Coverage targets**:
- `cli.py`: 80%+
- `setup/wizard.py`: 80%+

### Phase 5: Audio Processing 📋 PLANNED

**Focus**: Audio transcription and generation paths

**Files to create/enhance**:
- `tests/test_audio.py` - Audio functionality tests

**Coverage targets**:
- Audio processing modules: 80%+

### Phase 6: Rate Limiting 📋 PLANNED

**Focus**: Rate limiting with deterministic time control

**Files to create/enhance**:
- `tests/test_rate_limiting.py` - Rate limiting tests

**Coverage targets**:
- `rate_limiter.py`: 90%+
- Rate limiting integration: 80%+

## Test Architecture

### Fixtures Strategy

**Core fixtures in `conftest.py`**:
- `isolated_env` - Clears AI_* environment variables
- `tmp_workdir` - Temporary working directory
- `fake_provider` - Deterministic fake provider
- `fake_settings` - Test AiSettings with controlled defaults

### Test Patterns

**Unit Tests**:
- Small, focused, single responsibility
- Mock external dependencies at boundaries
- Test error conditions and edge cases

**Integration Tests**:
- Test component interactions
- Use real file system (temp dirs)
- Exercise config resolution end-to-end

**Determinism**:
- Fixed seeds for random operations
- Controlled time for rate limiting tests
- Predictable fake provider responses

### Coverage Configuration

**`.coveragerc` settings**:
```ini
[run]
source = src/ai_utilities
branch = True
omit = 
    */tests/*
    */test_*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

## Success Metrics

**Phase 1 Success Criteria**:
- Overall coverage: 40%+ (from 15%)
- Core modules (client, config, providers): 70%+
- All tests pass deterministically
- No network calls in test suite
- Test suite runs in < 30 seconds

**Final Success Criteria**:
- Overall coverage: 80%+
- All README features tested
- Zero flaky tests
- Complete test documentation
- Coverage includes error paths and edge cases

## Implementation Notes

### Testability Hooks

If production code changes are needed, they must be:
1. Minimal and focused
2. Well-documented as test-only features
3. Optional in production usage
4. Backward compatible

### Fake Provider Design

The `FakeProvider` should:
- Return deterministic responses based on input
- Support configurable delays for testing
- Simulate various error conditions
- Track call history for assertions
- Support both sync and async operations

### Environment Isolation

Each test must:
- Start with clean environment state
- Use monkeypatch for env var control
- Not depend on developer's actual environment
- Clean up temporary files and state

## Next Steps

1. **Phase 1 Implementation** (Current)
   - Create testing plan ✅
   - Implement Phase 1 tests
   - Verify coverage improvements
   - Ensure test stability

2. **Phase 2 Planning** (Next)
   - Design caching test strategy
   - Plan cache backend test matrix
   - Prepare fake provider enhancements

3. **Incremental Delivery**
   - Merge each phase separately
   - Monitor coverage progression
   - Maintain test quality standards
