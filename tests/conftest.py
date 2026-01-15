"""pytest configuration and fixtures for ai_utilities testing."""

import os
import sys
import tempfile
import asyncio
import logging
from pathlib import Path
from typing import Generator

import pytest

# Add src directory to Python path for imports
# This ensures tests import from the local src directory, not any installed version
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


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


# Test order independence verification
def pytest_configure(config):
    """Configure pytest for order independence testing."""
    # Add marker for order dependence tests
    config.addinivalue_line(
        "markers", "order_dependent: marks tests that verify order independence"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add order independence checks."""
    # Add a marker to track test order for debugging
    for i, item in enumerate(items):
        item.user_properties.append(("test_order", i))
