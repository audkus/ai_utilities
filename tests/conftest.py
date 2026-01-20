"""
pytest configuration and fixtures for ai_utilities tests.

This module provides common fixtures and test configuration for the ai_utilities test suite.
"""
from __future__ import annotations

import os
import sys
import pytest
import warnings
import logging
import socket
import tempfile
from unittest.mock import MagicMock, patch
from typing import Tuple, List
from pathlib import Path
from typing import Dict, Any, Iterator, Optional
import importlib
from types import ModuleType
from typing import Tuple


# Add src directory to Python path for imports
# This ensures tests import from the local src directory, not any installed version
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture
def openai_client_mod(openai_mocks: Tuple[MagicMock, MagicMock]) -> ModuleType:
    """
    Import ai_utilities.openai_client AFTER openai_mocks patching has run.

    This avoids stale module-object references when other tests reload modules.
    """
    import ai_utilities.openai_client as mod
    return importlib.import_module(mod.__name__)


@pytest.fixture
def openai_provider_mod(openai_mocks: Tuple[MagicMock, MagicMock]) -> ModuleType:
    """
    Import ai_utilities.providers.openai_provider AFTER openai_mocks has patched constructors.
    
    This prevents stale 'OpenAI = ...' alias bindings from earlier imports.
    """
    sys.modules.pop("ai_utilities.providers.openai_provider", None)
    return importlib.import_module("ai_utilities.providers.openai_provider")


def pytest_addoption(parser):
    """Add custom command line options for test guardrails."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require network access"
    )
    parser.addoption(
        "--allow-network",
        action="store_true", 
        default=False,
        help="Allow network connections during tests"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked as slow"
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests that require real network/API calls"
    )
    config.addinivalue_line(
        "markers", "skip_openai_global_patch: marks tests that should skip global OpenAI patching"
    )
    config.addinivalue_line(
        "markers", "order_dependent: marks tests that verify order independence"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers and order independence."""
    # Skip integration tests unless explicitly enabled
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    # Skip slow tests unless explicitly enabled
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    # Add a marker to track test order for debugging
    for i, item in enumerate(items):
        item.user_properties.append(("test_order", i))


@pytest.fixture(autouse=True)
def block_network(monkeypatch, request):
    """
    Block outbound network connections unless explicitly allowed.
    
    This fixture runs for all tests and blocks socket connections
    unless integration tests are enabled OR network is explicitly allowed.
    """
    # Check if network should be allowed
    integration_enabled = request.config.getoption("--run-integration")
    network_allowed = request.config.getoption("--allow-network")
    env_integration = os.getenv("AIU_RUN_INTEGRATION") == "1"
    
    allow_network = integration_enabled or network_allowed or env_integration
    
    if not allow_network:
        original_connect = socket.socket.connect
        
        def blocked_connect(self, *args, **kwargs):
            raise RuntimeError("Network connections blocked by default. Use --allow-network or --run-integration to enable.")
        
        monkeypatch.setattr(socket.socket, "connect", blocked_connect)


@pytest.fixture
def network_allowed():
    """
    Helper fixture for tests that explicitly opt-in to network access.
    
    This fixture does not block network connections, allowing individual
    tests to opt-in to network access even when not running integration tests.
    """
    # This fixture intentionally does nothing - the presence of this fixture
    # signals that the test allows network access
    pass


@pytest.fixture(autouse=True)
def patch_openai_aliases(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Autouse fixture that patches OpenAI constructors for tests that don't use openai_mocks.
    
    This provides a safety net to prevent real network calls while allowing
    per-test openai_mocks fixture to override for strict identity assertions.
    """
    # Early return if test explicitly uses openai_mocks fixture
    if "openai_mocks" in request.fixturenames:
        return
    
    # Early return if test has opt-out marker
    if request.node.get_closest_marker("skip_openai_global_patch"):
        return
    
    # Early return if integration/network access is allowed
    integration_enabled = request.config.getoption("--run-integration")
    network_allowed = request.config.getoption("--allow-network") 
    env_integration = os.getenv("AIU_RUN_INTEGRATION") == "1"
    if integration_enabled or network_allowed or env_integration:
        return
    
    # Create callable MagicMock for constructor
    ctor: MagicMock = MagicMock(name="Global_OpenAI_ctor")
    client: MagicMock = MagicMock(name="Global_OpenAI_client")
    ctor.return_value = client
    
    # Patch the critical module alias used by OpenAIClient
    try:
        import ai_utilities.openai_client as openai_client_mod
        monkeypatch.setattr(openai_client_mod, "OpenAI", ctor, raising=False)
    except ImportError:
        pass
    
    # Best-effort patch of upstream OpenAI module
    try:
        import openai
        monkeypatch.setattr(openai, "OpenAI", ctor, raising=False)
        monkeypatch.setattr(openai, "AsyncOpenAI", ctor, raising=False)
    except ImportError:
        pass


@pytest.fixture
def openai_mocks(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    reset_global_state: None,
    reset_contextvars: None,
    reset_logging_state: None,
) -> Tuple[MagicMock, MagicMock]:
    """Per-test OpenAI ctor/client mocks; patch the exact loaded module objects."""
    ctor: MagicMock = MagicMock(name="OpenAI_ctor_local")
    client: MagicMock = MagicMock(name="OpenAI_client_local")
    ctor.return_value = client

    # Patch upstream openai module (best effort)
    try:
        import openai
        monkeypatch.setattr(openai, "OpenAI", ctor, raising=False)
        monkeypatch.setattr(openai, "AsyncOpenAI", ctor, raising=False)
    except ImportError:
        pass

    # Patch *the exact module objects currently loaded* (avoid importing fresh copies)
    import sys

    for modname in (
        "ai_utilities.openai_client",
        "ai_utilities.providers.openai_provider",
        "ai_utilities.async_client",
    ):
        mod = sys.modules.get(modname)
        if mod is not None:
            monkeypatch.setattr(mod, "OpenAI", ctor, raising=False)
        else:
            # Debug: Module not loaded yet, try importing it
            try:
                imported_mod = __import__(modname, fromlist=["*"])
                monkeypatch.setattr(imported_mod, "OpenAI", ctor, raising=False)
            except ImportError:
                pass

    return ctor, client


@pytest.fixture(scope="session", autouse=True)
def enable_test_mode_guard():
    """
    Enable test-mode guards for the entire pytest session.
    
    This fixture automatically enables test mode when pytest is running,
    which activates warnings for:
    - Direct os.environ access
    - Nested environment overrides
    - Potential test isolation issues
    """
    # Import here to ensure coverage can track these modules
    import ai_utilities
    assert "src" in ai_utilities.__file__, "Tests should import from src directory, not installed package"
    
    # Import test-mode guard functionality
    from ai_utilities.env_overrides import test_mode_guard
    
    with test_mode_guard():
        yield


# Configure test logging
test_debug = os.getenv("AI_UTILITIES_TEST_DEBUG", "0") == "1"
if not test_debug:
    # Suppress logging during test collection unless debug mode is enabled
    logging.getLogger().setLevel(logging.CRITICAL)

# NOTE: .env file loading removed to allow proper test isolation
# Tests that need .env should use the temp_env_file fixture or load explicitly


@pytest.fixture
def isolated_env(monkeypatch):
    """Provide isolated environment by clearing all AI_* environment variables."""
    # Clear all AI_ environment variables
    env_vars_to_clear = [k for k in os.environ.keys() if k.startswith('AI_')]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    
    # Also clear common provider-specific vars that might interfere
    provider_vars = ['OPENAI_API_KEY', 'OPENAI_MODEL', 'OPENAI_BASE_URL']
    for var in provider_vars:
        monkeypatch.delenv(var, raising=False)
    
    return monkeypatch


@pytest.fixture
def tmp_workdir(tmp_path):
    """Provide a temporary working directory."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def fake_provider():
    """Provide a FakeProvider instance for testing."""
    from tests.fake_provider import FakeProvider
    return FakeProvider()


@pytest.fixture
def fake_settings():
    """Provide AiSettings with safe defaults for testing."""
    from ai_utilities import AiSettings
    return AiSettings(
        api_key="test-key-for-testing",
        model="gpt-3.5-turbo",
        temperature=0.7,
        timeout=30,
        _env_file=None  # Don't load from .env during tests
    )


@pytest.fixture
def fake_client(fake_settings, fake_provider):
    """Provide an AiClient with FakeProvider for offline testing."""
    from ai_utilities import AiClient
    return AiClient(settings=fake_settings, provider=fake_provider)


@pytest.fixture
def temp_env_file(tmp_workdir):
    """Create a temporary .env file for testing."""
    env_file = tmp_workdir / ".env"
    env_file.write_text("""
# Test environment variables
AI_PROVIDER=openai
AI_API_KEY=test-key-from-env-file
AI_MODEL=gpt-4
AI_TEMPERATURE=0.5
AI_MAX_TOKENS=1000
AI_BASE_URL=https://api.openai.com/v1
""")
    return env_file


@pytest.fixture
def env_with_file(temp_env_file, monkeypatch):
    """Load environment variables from a temporary .env file."""
    from dotenv import load_dotenv
    load_dotenv(temp_env_file)
    yield
    # Cleanup is handled by tmp_workdir fixture


@pytest.fixture
def memory_cache():
    """Provide a MemoryCache instance for testing."""
    from ai_utilities.cache import MemoryCache
    return MemoryCache(default_ttl_s=3600)


@pytest.fixture
def sqlite_cache(tmp_workdir):
    """Provide a SqliteCache instance for testing."""
    from ai_utilities.cache import SqliteCache
    db_path = tmp_workdir / "test_cache.db"
    return SqliteCache(db_path=db_path, namespace="test")


@pytest.fixture
def cache_settings_memory(isolated_env):
    """Provide AiSettings with memory cache enabled."""
    from ai_utilities import AiSettings
    return AiSettings(
        cache_enabled=True,
        cache_backend="memory",
        cache_ttl_s=3600,
        cache_max_temperature=0.7,
        _env_file=None
    )


@pytest.fixture
def cache_settings_sqlite(isolated_env, tmp_workdir):
    """Provide AiSettings with SQLite cache enabled."""
    from ai_utilities import AiSettings
    return AiSettings(
        cache_enabled=True,
        cache_backend="sqlite",
        cache_sqlite_path=tmp_workdir / "test.db",
        cache_ttl_s=3600,
        cache_max_temperature=0.7,
        cache_namespace="test",
        _env_file=None
    )


@pytest.fixture
def cached_client(cache_settings_memory, memory_cache):
    """Provide an AiClient with caching enabled."""
    from ai_utilities import AiClient
    return AiClient(settings=cache_settings_memory, cache=memory_cache)


@pytest.fixture
def fake_async_provider():
    """Provide a FakeAsyncProvider for testing."""
    from tests.fake_provider import FakeAsyncProvider
    return FakeAsyncProvider(responses=["Async response: {prompt}"])


@pytest.fixture
def fake_async_client(fake_settings, fake_async_provider):
    """Provide an AsyncAiClient with fake async provider."""
    from ai_utilities import AsyncAiClient
    return AsyncAiClient(settings=fake_settings, provider=fake_async_provider)


@pytest.fixture
def async_client_with_delay(fake_settings):
    """Provide an AsyncAiClient with delayed responses for timing tests."""
    from ai_utilities import AsyncAiClient
    from tests.fake_provider import FakeAsyncProvider
    provider = FakeAsyncProvider(responses=["Delayed: {prompt}"], delay=0.01)
    return AsyncAiClient(settings=fake_settings, provider=provider)


@pytest.fixture
def failing_async_provider(fake_settings):
    """Provide a FakeAsyncProvider that fails for error testing."""
    from tests.fake_provider import FakeAsyncProvider
    return FakeAsyncProvider(should_fail=True)




@pytest.fixture
def empty_env_file():
    """Provide an empty temporary .env file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_wizard_result():
    """Provide a mock SetupResult for testing."""
    from ai_utilities.setup.wizard import SetupResult
    return SetupResult(
        provider="openai",
        api_key="test-key-1234",
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo",
        dotenv_lines=[
            "AI_PROVIDER=openai",
            "AI_API_KEY=test-key-1234",
            "AI_MODEL=gpt-3.5-turbo"
        ]
    )


@pytest.fixture
def setup_wizard():
    """Provide a SetupWizard instance for testing."""
    from ai_utilities.setup.wizard import SetupWizard
    return SetupWizard()


# Test Isolation Fixtures - Added for Phase 2
# These fixtures ensure proper test isolation by resetting global state

@pytest.fixture(autouse=True)
def snapshot_restore_environment():
    """
    Automatically snapshot and restore os.environ around every test.
    
    This fixture runs before and after each test to ensure that
    environment variable mutations in one test don't affect others.
    """
    # Snapshot current environment
    original_env = dict(os.environ)
    
    yield
    
    # Restore environment to original state
    # Clear any added variables
    added_vars = set(os.environ.keys()) - set(original_env.keys())
    for var in added_vars:
        del os.environ[var]
    
    # Restore original values for existing variables
    for var, value in original_env.items():
        os.environ[var] = value


@pytest.fixture(autouse=True)
def reset_contextvars():
    """
    Reset contextvar state to known defaults before each test.
    
    This ensures contextvar pollution from one test doesn't affect
    subsequent tests.
    """
    try:
        from ai_utilities.env_overrides import _reset_all_overrides
        _reset_all_overrides()
    except ImportError:
        # Module not available - skip
        pass


@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Reset all global/module caches before each test.
    
    This fixture calls the comprehensive reset function to clear
    any cached state that might cause test pollution.
    """
    try:
        from ai_utilities._test_reset import reset_global_state_for_tests
        reset_global_state_for_tests()
    except ImportError:
        # Module not available - skip
        pass


@pytest.fixture(autouse=True)
def reset_logging_state():
    """
    Reset logging configuration to prevent test pollution.
    
    Some tests modify logging configuration which can affect
    subsequent tests. This fixture ensures clean logging state.
    """
    # Capture original logging state
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = list(root_logger.handlers)
    
    yield
    
    # Restore logging state
    root_logger.setLevel(original_level)
    
    # Remove any new handlers
    current_handlers = list(root_logger.handlers)
    for handler in current_handlers:
        if handler not in original_handlers:
            root_logger.removeHandler(handler)
    
    # Restore original handlers
    for handler in original_handlers:
        if handler not in root_logger.handlers:
            root_logger.addHandler(handler)


@pytest.fixture
def frozen_time():
    """
    Provide deterministic time for tests that depend on dates/times.
    
    This fixture patches time-related functions to return consistent
    values, preventing flaky tests due to time dependencies.
    """
    from datetime import datetime, date
    import time as time_module
    
    # Fixed time for testing
    fixed_datetime = datetime(2024, 1, 15, 10, 30, 0)
    fixed_date = date(2024, 1, 15)
    fixed_timestamp = fixed_datetime.timestamp()
    
    # Store original functions
    original_datetime_now = datetime.now
    original_date_today = date.today
    original_time_time = time_module.time
    
    def mock_datetime_now(tz=None):
        return fixed_datetime.replace(tzinfo=tz) if tz else fixed_datetime
    
    def mock_time():
        return fixed_timestamp
    
    # Apply patches
    datetime.now = mock_datetime_now
    date.today = lambda: fixed_date
    time_module.time = mock_time
    
    yield
    
    # Restore original functions
    datetime.now = original_datetime_now
    date.today = original_date_today
    time_module.time = original_time_time


@pytest.fixture
def clean_env(monkeypatch):
    """
    Fixture that provides a clean environment for testing.
    
    Unlike the autouse fixtures which preserve the original environment,
    this fixture provides a completely clean slate (no AI_ variables).
    
    Args:
        monkeypatch: pytest monkeypatch fixture
        
    Returns:
        monkeypatch fixture for additional environment setup
    """
    # Remove all AI_ environment variables
    ai_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
    for var in ai_vars:
        monkeypatch.delenv(var, raising=False)
    
    return monkeypatch


