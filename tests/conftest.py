"""
pytest configuration and fixtures for ai_utilities tests.

This module provides common fixtures and test configuration for the ai_utilities test suite.
"""
from __future__ import annotations

import importlib
import logging
import os
import socket
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest

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
    # Instead of removing from sys.modules, just force a reload if the module exists
    module_name = "ai_utilities.providers.openai_provider"
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    return importlib.import_module("ai_utilities.providers.openai_provider")


@pytest.fixture
def OpenAIClient(openai_client_mod: ModuleType):
    """Return the OpenAIClient class from freshly imported module."""
    return openai_client_mod.OpenAIClient


@pytest.fixture
def OpenAIProvider(openai_provider_mod: ModuleType):
    """Return the OpenAIProvider class from freshly imported module."""
    return openai_provider_mod.OpenAIProvider


def pytest_addoption(parser):
    """Add custom command line options for test guardrails."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require network access",
    )
    parser.addoption(
        "--allow-network",
        action="store_true",
        default=False,
        help="Allow network connections during tests",
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked as slow",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests that require real network/API calls",
    )
    config.addinivalue_line(
        "markers",
        "skip_openai_global_patch: marks tests that should skip global OpenAI patching",
    )
    config.addinivalue_line(
        "markers", "order_dependent: marks tests that verify order independence"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    
    # Register failure classification plugin
    try:
        # Ensure src is in Python path
        import sys
        from pathlib import Path
        src_path = str(Path(__file__).parent.parent / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
        plugin = FailureClassificationPlugin()
        config.pluginmanager.register(plugin, "failure_classification")
    except ImportError:
        # Plugin not available - skip registration
        pass


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers and order independence."""
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
        def blocked_connect(self, *args, **kwargs):
            raise RuntimeError(
                "Network connections blocked by default. Use --allow-network or --run-integration to enable."
            )

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


@pytest.fixture(autouse=True)
def patch_openai_aliases(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Autouse fixture that patches OpenAI constructors for tests that don't use openai_mocks.

    This provides a safety net to prevent real network calls while allowing
    per-test openai_mocks fixture to override for strict identity assertions.
    
    CRITICAL: Import ONLY inside fixture body to prevent early imports.
    """
    from unittest.mock import AsyncMock

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

    # Create AsyncMock for async constructor
    async_ctor: AsyncMock = AsyncMock(name="Global_AsyncOpenAI_ctor")
    async_ctor.return_value = client

    # Patch the critical module alias used by OpenAIClient
    try:
        # Import ONLY inside the fixture body to prevent early imports
        import ai_utilities.openai_client as openai_client_mod

        monkeypatch.setattr(openai_client_mod, "OpenAI", ctor, raising=False)
    except ImportError:
        pass

    # Best-effort patch of upstream OpenAI module
    try:
        import openai

        monkeypatch.setattr(openai, "OpenAI", ctor, raising=False)
        monkeypatch.setattr(openai, "AsyncOpenAI", async_ctor, raising=False)
    except ImportError:
        pass

    # Also patch async_client module if it's loaded
    try:
        import ai_utilities.async_client as async_client_mod
        monkeypatch.setattr(async_client_mod, "AsyncOpenAI", async_ctor, raising=False)
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
    from unittest.mock import AsyncMock

    ctor: MagicMock = MagicMock(name="OpenAI_ctor_local")
    client: MagicMock = MagicMock(name="OpenAI_client_local")
    ctor.return_value = client

    # Create AsyncMock for async OpenAI constructor
    async_ctor: AsyncMock = AsyncMock(name="AsyncOpenAI_ctor_local")
    async_client: AsyncMock = AsyncMock(name="AsyncOpenAI_client_local")
    async_ctor.return_value = async_client

    # Patch upstream openai module (best effort)
    try:
        import openai

        monkeypatch.setattr(openai, "OpenAI", ctor, raising=False)
        monkeypatch.setattr(openai, "AsyncOpenAI", async_ctor, raising=False)
    except ImportError:
        pass

    # Patch *the exact module objects currently loaded* (avoid importing fresh copies)
    import sys

    for modname in (
        "ai_utilities.openai_client",
        "ai_utilities.providers.openai_provider",
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

    # Special handling for async_client to use AsyncMock for async methods
    # Avoid importing the module if it might cause coroutine creation issues
    async_client_mod = sys.modules.get("ai_utilities.async_client")
    if async_client_mod is not None:
        # Use AsyncMock for AsyncOpenAI in async_client
        monkeypatch.setattr(async_client_mod, "AsyncOpenAI", async_ctor, raising=False)
    # NOTE: Removed the __import__ fallback to avoid potential coroutine creation during import

    return ctor, client


@pytest.fixture
def mock_openai_sdk_client():
    """
    Contract-level fixture for OpenAI SDK client mocking.
    
    Provides a mock client that matches the OpenAI SDK interface
    used by providers, without importing openai at module load time.
    """
    from unittest.mock import MagicMock
    
    # Mock client with the exact interface used by providers
    mock_client = MagicMock()
    
    # Mock chat completions response structure
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test response"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    # Mock file operations
    mock_file = MagicMock()
    mock_file.id = "file-123"
    mock_file.filename = "test.txt"
    mock_file.bytes = 1024
    mock_client.files.create.return_value = mock_file
    mock_client.files.retrieve.return_value = mock_file
    mock_client.files.delete.return_value = MagicMock(deleted=True)
    
    # Mock image generation
    mock_image_response = MagicMock()
    mock_image = MagicMock()
    mock_image.url = "https://example.com/image.png"
    mock_image_response.data = [mock_image]
    mock_client.images.generate.return_value = mock_image_response
    
    return mock_client


@pytest.fixture
def settings_minimal():
    """
    Minimal AiSettings for contract testing.

    Provides only the required fields for provider creation,
    avoiding optional dependencies and complex configuration.
    """
    from ai_utilities.config_models import AiSettings
    
    return AiSettings(
        provider="openai",
        api_key="test-key",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000,
        timeout=30
    )


@pytest.fixture
def mock_openai_compatible_response():
    """
    Contract-level fixture for OpenAI Compatible provider response mocking.
    
    Provides real response objects with proper string content that match
    the provider's parsing contract, avoiding MagicMock chains.
    """
    from types import SimpleNamespace
    
    # Create response structure with real strings
    message = SimpleNamespace(content="Test response content")
    choice = SimpleNamespace(message=message)
    response = SimpleNamespace(choices=[choice])
    
    return response


@pytest.fixture
def mock_openai_compatible_json_response():
    """
    Contract-level fixture for OpenAI Compatible provider JSON response mocking.
    
    Provides real response objects with JSON string content that match
    the provider's JSON parsing contract.
    """
    from types import SimpleNamespace
    import json
    
    # Create response structure with JSON string content
    json_content = json.dumps({"key": "value", "number": 123})
    message = SimpleNamespace(content=json_content)
    choice = SimpleNamespace(message=message)
    response = SimpleNamespace(choices=[choice])
    
    return response


@pytest.fixture
def mock_openai_compatible_client(mock_openai_compatible_response, mock_openai_compatible_json_response):
    """
    Contract-level fixture for OpenAI Compatible provider client mocking.
    
    Provides a mock client that returns proper response objects with real strings,
    matching the provider's parsing contract without MagicMock chains.
    """
    from unittest.mock import MagicMock
    
    # Mock client with proper response objects
    mock_client = MagicMock()
    
    # Set up chat completions to return appropriate responses
    def create_chat_completion(**kwargs):
        # Return JSON response if response_format is json_object, otherwise text
        if kwargs.get("response_format", {}).get("type") == "json_object":
            return mock_openai_compatible_json_response
        return mock_openai_compatible_response
    
    mock_client.chat.completions.create.side_effect = create_chat_completion
    
    return mock_client


@pytest.fixture
def patch_openai_sdk_client():
    """
    Fixture that patches OpenAI provider's SDK client creation boundary.
    
    Patches the stable _create_openai_sdk_client function, ensuring the provider
    uses our mock client with SimpleNamespace response objects to avoid leaks.
    """
    from unittest.mock import patch
    from types import SimpleNamespace
    
    # Create deterministic fake client with SimpleNamespace responses
    mock_client = SimpleNamespace()
    
    # Mock chat completions with SimpleNamespace to avoid MagicMock leaks
    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Test response"))]
    )
    mock_client.chat = SimpleNamespace()
    mock_client.chat.completions = SimpleNamespace()
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)
    
    # Mock file operations
    mock_file = SimpleNamespace(id="file-123", filename="test.txt", bytes=1024)
    mock_client.files = SimpleNamespace()
    mock_client.files.create = MagicMock(return_value=mock_file)
    mock_client.files.retrieve = MagicMock(return_value=mock_file)
    mock_client.files.delete = MagicMock(return_value=SimpleNamespace(deleted=True))
    
    # Mock image generation
    mock_image = SimpleNamespace(url="https://example.com/image.png")
    mock_client.images = SimpleNamespace()
    mock_client.images.generate = MagicMock(return_value=SimpleNamespace(data=[mock_image]))
    
    with patch('ai_utilities.providers.openai_provider._create_openai_sdk_client') as mock_create:
        mock_create.return_value = mock_client
        yield mock_create


@pytest.fixture
def patch_openai_compatible_sdk_client():
    """
    Fixture that patches OpenAI Compatible provider's SDK client creation boundary.
    
    Patches the stable _create_openai_sdk_client function, ensuring the provider
    uses our mock client with SimpleNamespace response objects to avoid leaks.
    """
    from unittest.mock import patch
    from types import SimpleNamespace
    
    # Create deterministic fake client with SimpleNamespace responses
    mock_client = SimpleNamespace()
    
    # Mock chat completions with SimpleNamespace to avoid MagicMock leaks
    def create_chat_completion(**kwargs):
        if kwargs.get("response_format", {}).get("type") == "json_object":
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"test": "json"}'))]
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Test response"))]
        )
    
    mock_client.chat = SimpleNamespace()
    mock_client.chat.completions = SimpleNamespace()
    mock_client.chat.completions.create = MagicMock(side_effect=create_chat_completion)
    
    # Mock file operations
    mock_file = SimpleNamespace(id="file-123", filename="test.txt", bytes=1024)
    mock_client.files = SimpleNamespace()
    mock_client.files.create = MagicMock(return_value=mock_file)
    mock_client.files.retrieve = MagicMock(return_value=mock_file)
    mock_client.files.delete = MagicMock(return_value=SimpleNamespace(deleted=True))
    
    # Mock image generation
    mock_image = SimpleNamespace(url="https://example.com/image.png")
    mock_client.images = SimpleNamespace()
    mock_client.images.generate = MagicMock(return_value=SimpleNamespace(data=[mock_image]))
    
    with patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client') as mock_create:
        mock_create.return_value = mock_client
        yield mock_create


@pytest.fixture
def auto_patch_openai_boundary_functions():
    """
    Fixture that patches OpenAI boundary functions for tests.
    
    This ensures that tests can instantiate OpenAI-compatible providers without
    requiring the openai package to be installed, and avoids MagicMock leaks.
    
    Use this fixture in tests that need OpenAI providers:
    
    @pytest.mark.usefixtures("auto_patch_openai_boundary_functions")
    def test_something():
        # Test code here
    """
    from unittest.mock import patch
    from types import SimpleNamespace
    
    # Create deterministic fake client for OpenAI provider
    mock_openai_client = SimpleNamespace()
    mock_openai_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Test response"))]
    )
    mock_openai_client.chat = SimpleNamespace()
    mock_openai_client.chat.completions = SimpleNamespace()
    mock_openai_client.chat.completions.create = MagicMock(return_value=mock_openai_response)
    
    # Create deterministic fake client for OpenAI Compatible provider
    mock_compatible_client = SimpleNamespace()
    
    def create_chat_completion(**kwargs):
        if kwargs.get("response_format", {}).get("type") == "json_object":
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"test": "json"}'))]
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Test response"))]
        )
    
    mock_compatible_client.chat = SimpleNamespace()
    mock_compatible_client.chat.completions = SimpleNamespace()
    mock_compatible_client.chat.completions.create = MagicMock(side_effect=create_chat_completion)
    
    # Import the modules to ensure they exist before patching
    try:
        import ai_utilities.providers.openai_provider
        import ai_utilities.providers.openai_compatible_provider
        
        # Patch both boundary functions
        with patch('ai_utilities.providers.openai_provider._create_openai_sdk_client') as mock_openai_create, \
             patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client') as mock_compatible_create:
            mock_openai_create.return_value = mock_openai_client
            mock_compatible_create.return_value = mock_compatible_client
            yield
    except ImportError:
        # If modules can't be imported, skip patching (tests that need them will fail appropriately)
        yield


@pytest.fixture
def reset_openai_client_globals():
    """
    Reset ai_utilities.openai_client global state between tests.
    
    This fixture ensures that tests that patch the lazy loading mechanism
    don't leak state to other tests.
    """
    import ai_utilities.openai_client
    
    # Store original values
    original_openai = ai_utilities.openai_client._openai
    original_openai_class = ai_utilities.openai_client.OpenAI
    
    try:
        yield
    finally:
        # Reset to original values
        ai_utilities.openai_client._openai = original_openai
        ai_utilities.openai_client.OpenAI = original_openai_class


@pytest.fixture
def enable_test_mode_guard():
    """
    Enable test-mode guards for tests that use this fixture.

    This fixture enables test mode when pytest is running,
    which activates warnings for:
    - Direct os.environ access
    - Nested environment overrides
    - Potential test isolation issues
    
    IMPORTANT: Not autouse and function-scoped to prevent early imports
    before coverage measurement starts. Tests that need test mode guards
    must explicitly use this fixture.
    """
    # Import ONLY inside the fixture body to prevent early imports
    import ai_utilities

    assert "src" in ai_utilities.__file__, (
        "Tests should import from src directory, not installed package"
    )

    # Import test-mode guard functionality
    from ai_utilities.env_overrides import test_mode_guard as _test_mode_guard

    with _test_mode_guard():
        yield


# Configure test logging
test_debug = os.getenv("AI_UTILITIES_TEST_DEBUG", "0") == "1"
if not test_debug:
    # Suppress logging during test collection unless debug mode is enabled
    logging.getLogger().setLevel(logging.CRITICAL)

# NOTE: .env file loading removed to allow proper test isolation
# Tests that need .env should use the temp_env_file fixture or load explicitly


@pytest.fixture(scope="session", autouse=True)
def load_dotenv_opt_in():
    """
    Centralized opt-in .env loader for integration tests.
    
    Only loads .env when AI_UTILITIES_LOAD_DOTENV=1 is set.
    This keeps unit tests deterministic while allowing integration tests to opt-in.
    """
    if os.getenv("AI_UTILITIES_LOAD_DOTENV") == "1":
        try:
            from dotenv import load_dotenv
        except ImportError:
            # python-dotenv not installed - quiet no-op
            return
        
        # Compute repo root robustly (tests/conftest.py -> tests/ -> repo root)
        repo_root = Path(__file__).resolve().parent.parent
        env_file = repo_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file, override=False)


@pytest.fixture
def isolated_env(monkeypatch):
    """Provide isolated environment by clearing all AI_* environment variables."""
    # Clear all AI_ environment variables
    env_vars_to_clear = [k for k in os.environ.keys() if k.startswith("AI_")]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Also clear common provider-specific vars that might interfere
    provider_vars = [
        "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL",
        "TEXT_GENERATION_WEBUI_BASE_URL", "TEXT_GENERATION_WEBUI_MODEL",
        "FASTCHAT_BASE_URL", "FASTCHAT_MODEL",
        "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "LMSTUDIO_BASE_URL", "LMSTUDIO_MODEL",
        "VLLM_BASE_URL", "OOBABOOGA_BASE_URL"
    ]
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
        _env_file=None,  # Don't load from .env during tests
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
        _env_file=None,
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
        _env_file=None,
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
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
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
            "AI_MODEL=gpt-3.5-turbo",
        ],
    )


@pytest.fixture
def setup_wizard():
    """Provide a SetupWizard instance for testing."""
    from ai_utilities.setup.wizard import SetupWizard

    return SetupWizard()


# Test Isolation Fixtures - Added for Phase 2
# These fixtures ensure proper test isolation by resetting global state


# @pytest.fixture(autouse=True)
# def snapshot_restore_environment():
#     """
#     Automatically snapshot and restore os.environ around every test.
#
#     This fixture runs before and after each test to ensure that
#     environment variable mutations in one test don't affect others.
#     """
#     # Load .env file before taking snapshot to ensure .env variables are included
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#     except ImportError:
#         pass  # dotenv not available
#     
#     # Ensure RUN_LIVE_AI_TESTS is set if provided in shell
#     if os.getenv("RUN_LIVE_AI_TESTS") == "1":
#         os.environ["RUN_LIVE_AI_TESTS"] = "1"
#     
#     # Snapshot current environment (after .env loading)
#     original_env = dict(os.environ)
#
#     yield
#
#     # Restore environment to original state
#     # Clear any added variables
#     added_vars = set(os.environ.keys()) - set(original_env.keys())
#     for var in added_vars:
#         del os.environ[var]
#
#     # Restore original values for existing variables
#     for var, value in original_env.items():
#         os.environ[var] = value


@pytest.fixture(autouse=True)
def reset_contextvars():
    """
    Reset contextvar state to known defaults before each test.

    This ensures contextvar pollution from one test doesn't affect
    subsequent tests.
    
    CRITICAL: Import ONLY inside fixture body to prevent early imports.
    """
    try:
        # Import ONLY inside the fixture body to prevent early imports
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
    
    CRITICAL: Import ONLY inside fixture body to prevent early imports.
    """
    try:
        # Import ONLY inside the fixture body to prevent early imports
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


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    """
    Automatically isolate environment variables for all tests.
    
    This fixture ensures that environment variables from .env files
    or other tests don't contaminate subsequent tests. It clears
    all AI-related environment variables before each test.
    
    IMPORTANT: This fixture runs AFTER reset_global_state to ensure
    any environment variables restored by global state reset are cleared.
    """
    # Clear all AI_ environment variables
    env_vars_to_clear = [k for k in os.environ.keys() if k.startswith("AI_")]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Also clear common provider-specific vars that might interfere
    provider_vars = [
        "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL",
        "TEXT_GENERATION_WEBUI_BASE_URL", "TEXT_GENERATION_WEBUI_MODEL",
        "FASTCHAT_BASE_URL", "FASTCHAT_MODEL",
        "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "LMSTUDIO_BASE_URL", "LMSTUDIO_MODEL",
        "VLLM_BASE_URL", "OOBABOOGA_BASE_URL"
    ]
    for var in provider_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def frozen_time():
    """
    Provide deterministic time for tests that depend on dates/times.

    This fixture patches time-related functions to return consistent
    values, preventing flaky tests due to time dependencies.
    """
    import time as time_module
    from datetime import date, datetime

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


# Repository root allowlists for test hygiene enforcement
ROOT_FILE_ALLOWLIST = {
    ".gitignore",
    ".pre-commit-config.yaml",
    ".env.example",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "MANIFEST.in",
    "Makefile",
    "MIGRATION.md",
    "README.md",
    "RELEASE.md",
    "RELEASE_CHECKLIST.md",
    "SUPPORT.md",
    "pyproject.toml",
    "pytest.ini",
    "tox.ini",
    ".coveragerc",  # Keep only ONE coverage config file
}

ROOT_DIR_ALLOWED_DIRECTORIES = {
    ".git",
    ".github",
    "src",
    "tests",
    "docs",
    "scripts",
    "examples",
    "tools",
    "reports",
    "coverage_reports",
    ".pytest_cache",  # Allow pytest cache directory
}

# Transient files allowed during test run but must be cleaned up
TRANSIENT_FILES = {
    ".coverage",
    ".coverage.*",  # Coverage files with process IDs
    "htmlcov",  # Coverage HTML reports (default location)
}

# Allowed write paths under repo root
ALLOWED_WRITE_PATHS = {
    "coverage_reports/**",
    "reports/**",
    # Note: .pytest_cache handled by pytest.ini ignore patterns
}


@pytest.fixture(scope="session", autouse=True)
def enforce_repo_root_cleanliness() -> None:
    """Session-level guard to ensure repo root stays clean.

    - Snapshots repo root state at session start.
    - At session end, removes known transient artifacts created by tools
      (e.g. `.coverage*` from `coverage run`) if they were created during this run.
    - Fails if any other unauthorized files/dirs appear in repo root.

    Raises:
        AssertionError: If unauthorized files/dirs found in repo root.
    """
    import fnmatch

    def get_repo_root() -> Path:
        """Get repository root by walking up from conftest.py."""
        conftest_path: Path = Path(__file__).resolve()
        current: Path = conftest_path.parent
        while current.parent != current.root and not (current / "pyproject.toml").exists():
            current = current.parent
        return current

    repo_root: Path = get_repo_root()

    def snapshot_root(root: Path) -> tuple[set[str], set[str]]:
        files: set[str] = set()
        dirs: set[str] = set()
        for item in root.iterdir():
            if item.is_file():
                files.add(item.name)
            elif item.is_dir():
                dirs.add(item.name)
        return files, dirs

    initial_files, initial_dirs = snapshot_root(repo_root)

    yield

    # 1) Auto-clean transient artifacts created during *this* run (best-effort).
    #    This makes `coverage run -m pytest` compatible with the root policy.
    created_during_run: set[str] = set()
    final_files_pre, _final_dirs_pre = snapshot_root(repo_root)
    created_during_run = final_files_pre - initial_files

    transient_created: list[Path] = []
    for name in sorted(created_during_run):
        if any(fnmatch.fnmatch(name, pattern) for pattern in TRANSIENT_FILES):
            transient_created.append(repo_root / name)

    transient_delete_failures: list[str] = []
    for path in transient_created:
        try:
            if path.is_dir():
                import shutil
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        except OSError as exc:  # pragma: no cover
            transient_delete_failures.append(f"{path.name} ({exc})")

    if transient_delete_failures:
        raise AssertionError(
            "Repository root contamination detected!\n"
            f"Repository root: {repo_root}\n"
            f"Could not delete transient files: {sorted(transient_delete_failures)}\n"
            "Delete them manually and re-run.\n"
            f"Transient patterns: {sorted(TRANSIENT_FILES)}"
        )

    # 2) Re-snapshot after cleanup and enforce allowlists.
    final_files, final_dirs = snapshot_root(repo_root)

    new_files = final_files - initial_files - ROOT_FILE_ALLOWLIST
    new_dirs = final_dirs - initial_dirs - ROOT_DIR_ALLOWED_DIRECTORIES

    # Remove transient patterns from `new_files` (even if tool recreated them late).
    new_files = {
        f for f in new_files
        if not any(fnmatch.fnmatch(f, pattern) for pattern in TRANSIENT_FILES)
    }

    if new_files or new_dirs:
        error_parts: list[str] = []
        if new_files:
            error_parts.append(f"Unauthorized files: {sorted(new_files)}")
        if new_dirs:
            error_parts.append(f"Unauthorized directories: {sorted(new_dirs)}")

        raise AssertionError(
            "Repository root contamination detected!\n"
            f"Repository root: {repo_root}\n"
            f"{'. '.join(error_parts)}\n"
            f"Allowed files: {sorted(ROOT_FILE_ALLOWLIST)}\n"
            f"Allowed directories: {sorted(ROOT_DIR_ALLOWED_DIRECTORIES)}\n"
            "Use tmp_path, tmp_path_factory, or reports/ for outputs."
        )


@pytest.fixture(autouse=True)
def prevent_root_artifacts(tmp_path, monkeypatch):
    """Prevent tests from creating artifacts in repository root.
    
    This fixture blocks writes to repository root by patching file operations
    and ensuring tests run in a safe temporary working directory.
    
    Args:
        tmp_path: pytest temporary directory fixture
        monkeypatch: pytest monkeypatch fixture
        
    Raises:
        AssertionError: If test attempts to write to repository root
    """
    import fnmatch
    from pathlib import Path

    # Robust repository root detection
    def get_repo_root():
        """Get repository root with multiple fallback strategies."""
        # Strategy 1: Walk up from conftest.py location
        conftest_path = Path(__file__).resolve()
        current = conftest_path.parent
        while current.parent != current.root and not (current / "pyproject.toml").exists():
            current = current.parent

        # Strategy 2: Try git root
        try:
            import subprocess
            git_root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=conftest_path.parent
            )
            if git_root.returncode == 0:
                return Path(git_root.stdout.strip())
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Strategy 3: Fallback to conftest parent
        return conftest_path.parent

    repo_root = get_repo_root()

    # Change working directory to tmp_path for safety
    monkeypatch.chdir(tmp_path)

    def is_path_allowed(path):
        """Check if a path is allowed for write operations."""
        if not path:
            return False

        try:
            resolved_path = Path(path).resolve()
        except (OSError, ValueError):
            resolved_path = Path(path)

        # Convert to absolute if relative
        if not resolved_path.is_absolute():
            resolved_path = Path.cwd() / resolved_path
            resolved_path = resolved_path.resolve()

        # Check if path is under repo root
        try:
            resolved_path.relative_to(repo_root)
            # Path is under repo root - check if it's allowed
            relative_path = str(resolved_path.relative_to(repo_root))

            # Check against allowed patterns
            for pattern in ALLOWED_WRITE_PATHS:
                if fnmatch.fnmatch(relative_path, pattern):
                    return True
                # Also check if path starts with allowed directory
                if relative_path.startswith(pattern.replace("**", "").rstrip("/")):
                    return True

            # Check if it's a transient file in root
            if resolved_path.parent == repo_root:
                for pattern in TRANSIENT_FILES:
                    if fnmatch.fnmatch(resolved_path.name, pattern):
                        return True

            return False  # Unsafe path under repo root
        except ValueError:
            # Path is not under repo root - safe
            return True

    def safe_open_wrapper(original_open, file, mode='r', *args, **kwargs):
        """Wrapper for open() that blocks unsafe writes."""
        if 'w' in mode or 'a' in mode or 'x' in mode or '+' in mode:
            if not is_path_allowed(file):
                raise AssertionError(
                    f"Test attempted to write to repository root: {file}\n"
                    f"Repository root: {repo_root}\n"
                    f"Current working directory: {Path.cwd()}\n"
                    f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
                )
        return original_open(file, mode, *args, **kwargs)

    # Store original methods before patching
    import builtins
    original_open = builtins.open
    original_write_text = Path.write_text
    original_write_bytes = Path.write_bytes
    original_mkdir = Path.mkdir
    original_rename = Path.rename
    original_replace = Path.replace
    original_touch = Path.touch

    monkeypatch.setattr(builtins, 'open', lambda file, mode='r', *args, **kwargs:
                       safe_open_wrapper(original_open=original_open, file=file, mode=mode, *args, **kwargs))

    def safe_write_text_wrapper(self, data, encoding=None, errors=None):
        """Wrapper for Path.write_text() that blocks unsafe writes."""
        if not is_path_allowed(self):
            raise AssertionError(
                f"Test attempted to write_text to repository root: {self}\n"
                f"Repository root: {repo_root}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
            )
        return original_write_text(self, data, encoding, errors)

    def safe_write_bytes_wrapper(self, data):
        """Wrapper for Path.write_bytes() that blocks unsafe writes."""
        if not is_path_allowed(self):
            raise AssertionError(
                f"Test attempted to write_bytes to repository root: {self}\n"
                f"Repository root: {repo_root}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
            )
        return original_write_bytes(self, data)

    def safe_mkdir_wrapper(self, mode=0o777, parents=False, exist_ok=False):
        """Wrapper for Path.mkdir() that blocks unsafe directory creation."""
        if not is_path_allowed(self):
            raise AssertionError(
                f"Test attempted to create directory in repository root: {self}\n"
                f"Repository root: {repo_root}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
            )
        return original_mkdir(self, mode, parents, exist_ok)

    def safe_rename_wrapper(self, target):
        """Wrapper for Path.rename() that blocks unsafe renames."""
        if not is_path_allowed(self) or not is_path_allowed(target):
            raise AssertionError(
                f"Test attempted to rename file in repository root: {self} -> {target}\n"
                f"Repository root: {repo_root}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
            )
        return original_rename(self, target)

    def safe_replace_wrapper(self, target):
        """Wrapper for Path.replace() that blocks unsafe replacements."""
        if not is_path_allowed(self) or not is_path_allowed(target):
            raise AssertionError(
                f"Test attempted to replace file in repository root: {self} -> {target}\n"
                f"Repository root: {repo_root}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
            )
        return original_replace(self, target)

    def safe_touch_wrapper(self, mode=0o666, exist_ok=True):
        """Wrapper for Path.touch() that blocks unsafe touches."""
        if not is_path_allowed(self):
            raise AssertionError(
                f"Test attempted to touch file in repository root: {self}\n"
                f"Repository root: {repo_root}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Use tmp_path, tmp_path_factory, or reports/ for outputs."
            )
        return original_touch(self, mode, exist_ok)

    monkeypatch.setattr(Path, 'write_text', safe_write_text_wrapper, raising=False)
    monkeypatch.setattr(Path, 'write_bytes', safe_write_bytes_wrapper, raising=False)
    monkeypatch.setattr(Path, 'mkdir', safe_mkdir_wrapper, raising=False)
    monkeypatch.setattr(Path, 'rename', safe_rename_wrapper, raising=False)
    monkeypatch.setattr(Path, 'replace', safe_replace_wrapper, raising=False)
    monkeypatch.setattr(Path, 'touch', safe_touch_wrapper, raising=False)

    yield


@pytest.fixture(autouse=True)
def _no_env_leaks_diagnostic(request: pytest.FixtureRequest):
    """
    Diagnostic environment leak detection.
    
    This fixture monitors environment variable changes but only reports them
    in strict mode (AI_UTILITIES_STRICT_ENV=1). By default, it silently
    restores the environment to prevent test pollution.
    
    Use AI_UTILITIES_STRICT_ENV=1 to enable strict mode for debugging.
    
    Note: This fixture runs after reset_global_state, so we ignore environment
    changes caused by the global state reset to avoid false positives.
    """
    import os
    from collections.abc import Generator
    from typing import Dict, Iterable, Tuple
    
    def _redact(value: str) -> str:
        if value is None:
            return "<none>"
        if len(value) <= 3:
            return "***"
        return f"{value[:3]}***({len(value)})"

    def _diff_env(
        before: Dict[str, str],
        after: Dict[str, str],
        keys: Iterable[str],
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Tuple[str, str]]]:
        added: Dict[str, str] = {}
        removed: Dict[str, str] = {}
        changed: Dict[str, Tuple[str, str]] = {}

        for k in keys:
            b = before.get(k)
            a = after.get(k)
            if b is None and a is not None:
                added[k] = a
            elif b is not None and a is None:
                removed[k] = b
            elif b is not None and a is not None and b != a:
                changed[k] = (b, a)

        return added, removed, changed

    # Environment variables to monitor
    watched = (
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL", 
        "OPENAI_MODEL",
        "AI_PROVIDER",
        "AI_MODEL",
        "GROQ_API_KEY",
        "TOGETHER_API_KEY",
        "OPENROUTER_API_KEY",
        "OLLAMA_HOST",
        "ANTHROPIC_API_KEY",
        "AI_API_KEY",
        "TEXT_GENERATION_WEBUI_BASE_URL",
        "LMSTUDIO_BASE_URL",
        "FASTCHAT_BASE_URL",
    )
    
    before: Dict[str, str] = dict(os.environ)
    strict_mode = os.environ.get("AI_UTILITIES_STRICT_ENV") == "1"
    
    try:
        yield
    finally:
        after: Dict[str, str] = dict(os.environ)
        added, removed, changed = _diff_env(before, after, watched)

        # Always restore environment deterministically
        os.environ.clear()
        os.environ.update(before)

        # Only fail in strict mode for real leaks (not caused by global state reset)
        if strict_mode and (added or removed or changed):
            # Check if this looks like a global state reset (removing AI_* variables)
            # The global state reset clears environment variables, so any removal of AI_* vars is likely from it
            is_global_reset = (
                len(removed) >= 1 and 
                any(var.startswith(('OPENAI_', 'AI_', 'GROQ_', 'TOGETHER_', 'ANTHROPIC_')) for var in removed.keys())
            )
            
            if not is_global_reset:
                lines = [f"ENV LEAK in {request.node.nodeid}"]
                if added:
                    lines.append("  Added:")
                    for k, v in sorted(added.items()):
                        lines.append(f"    {k}={_redact(v)}")
                if removed:
                    lines.append("  Removed:")
                    for k, v in sorted(removed.items()):
                        lines.append(f"    {k}={_redact(v)}")
                if changed:
                    lines.append("  Changed:")
                    for k, (b, a) in sorted(changed.items()):
                        lines.append(f"    {k}: {_redact(b)} -> {_redact(a)}")
                raise AssertionError("\n".join(lines))
        elif added or removed or changed:
            # Diagnostic mode: just warn without failing for real leaks
            # Check if this looks like a global state reset
            is_global_reset = (
                len(removed) >= 1 and 
                any(var.startswith(('OPENAI_', 'AI_', 'GROQ_', 'TOGETHER_', 'ANTHROPIC_')) for var in removed.keys())
            )
            
            if not is_global_reset:
                lines = [f"ENV LEAK DETECTED (diagnostic): {request.node.nodeid}"]
                if added:
                    lines.append("  Added:")
                    for k, v in sorted(added.items()):
                        lines.append(f"    {k}={_redact(v)}")
                if removed:
                    lines.append("  Removed:")
                    for k, v in sorted(removed.items()):
                        lines.append(f"    {k}={_redact(v)}")
                if changed:
                    lines.append("  Changed:")
                    for k, (b, a) in sorted(changed.items()):
                        lines.append(f"    {k}: {_redact(b)} -> {_redact(a)}")
                print("\n".join(lines))


@pytest.fixture(autouse=True)
def reset_metrics_registry():
    """
    Reset the metrics registry between tests to prevent test pollution.
    
    The MetricsRegistry is a singleton that accumulates metrics across tests,
    so we need to reset it to ensure test isolation.
    """
    try:
        from ai_utilities.metrics import MetricsRegistry
        registry = MetricsRegistry()
        registry.reset()
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
    ai_vars = [k for k in os.environ.keys() if k.startswith("AI_")]
    for var in ai_vars:
        monkeypatch.delenv(var, raising=False)

    return monkeypatch


def requires_openai() -> bool:
    """
    Check if OpenAI-dependent tests should be run.
    
    Returns:
        True if RUN_OPENAI_TESTS environment variable is set to truthy value
    """
    return bool(os.getenv("RUN_OPENAI_TESTS"))


def pytest_runtest_setup(item):
    """
    Skip tests that require OpenAI if RUN_OPENAI_TESTS is not set.
    """
    if "requires_openai" in item.keywords and not requires_openai():
        pytest.skip("Test requires OpenAI SDK - set RUN_OPENAI_TESTS=1 to run")


@pytest.fixture(scope="session", autouse=True)
def ensure_coverage_reports_directory():
    """
    Session-scoped autouse fixture to ensure coverage_reports/ directory exists.
    
    This prevents coverage DataError when pytest-cov tries to write fragment files
    to a non-existent coverage_reports/ directory, especially under parallel/xdist behavior.
    
    The fixture:
    - Creates coverage_reports/ if it doesn't exist
    - Removes stale .coverage* files to avoid combine conflicts
    - Does NOT delete the directory itself
    """
    # Compute project root (tests/conftest.py -> tests/ -> project root)
    project_root = Path(__file__).resolve().parents[2]
    coverage_reports_dir = project_root / "coverage_reports"
    
    # Ensure directory exists
    coverage_reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove stale coverage data files to avoid combine conflicts
    for stale_file in coverage_reports_dir.glob(".coverage*"):
        try:
            stale_file.unlink()
        except OSError:
            # Ignore cleanup errors
            pass


@pytest.fixture
def force_openai_missing():
    """
    Fixture to deterministically simulate missing OpenAI dependency.
    
    This fixture ensures that OpenAIProvider and create_provider raise
    MissingOptionalDependencyError even when openai package is installed
    in the test environment.
    
    Usage:
        def test_openai_missing(force_openai_missing):
            with pytest.raises(MissingOptionalDependencyError):
                OpenAIProvider(settings)
    """
    import sys
    import importlib.abc
    import importlib.machinery
    
    # Store original state for cleanup
    original_meta_path = sys.meta_path.copy()
    original_modules = {}
    
    # Remove openai modules from sys.modules
    keys_to_remove = [k for k in sys.modules.keys() if k == "openai" or k.startswith("openai.")]
    for key in keys_to_remove:
        original_modules[key] = sys.modules.pop(key)
    
    class OpenAIBlockFinder(importlib.abc.MetaPathFinder):
        """MetaPathFinder that blocks openai imports."""
        
        def find_spec(self, fullname, path, target=None):
            if fullname == "openai" or fullname.startswith("openai."):
                raise ModuleNotFoundError(f"No module named '{fullname}' (OpenAI blocked for testing)")
            return None
    
    # Insert the blocker at the front of meta_path
    blocker = OpenAIBlockFinder()
    sys.meta_path.insert(0, blocker)
    
    try:
        yield
    finally:
        # Cleanup: remove the blocker
        if blocker in sys.meta_path:
            sys.meta_path.remove(blocker)
        
        # Restore original meta_path order
        sys.meta_path[:] = original_meta_path
        
        # Restore original modules (only if they don't exist)
        for key, module in original_modules.items():
            if key not in sys.modules:
                sys.modules[key] = module


@pytest.fixture
def dummy_provider():
    """Provide a DummyProvider instance for testing."""
    from tests.utils.dummy_provider import DummyProvider
    return DummyProvider()


@pytest.fixture
def dummy_async_provider():
    """Provide an AsyncDummyProvider instance for testing."""
    from tests.utils.dummy_provider import AsyncDummyProvider
    return AsyncDummyProvider()


@pytest.fixture
def dummy_settings():
    """Provide AiSettings configured for dummy provider."""
    from ai_utilities.config_models import AiSettings
    return AiSettings(provider="dummy", api_key="dummy-key", model="dummy-model")


@pytest.fixture
def ai_client_with_fake_provider(fake_provider):
    """Provide an AiClient with explicit FakeProvider for unit tests."""
    from ai_utilities import AiClient, AiSettings
    settings = AiSettings(api_key="test-key", model="test-model")
    return AiClient(settings, provider=fake_provider)


@pytest.fixture
def async_ai_client_with_fake_provider(fake_async_provider):
    """Provide an AsyncAiClient with explicit FakeAsyncProvider for unit tests."""
    from ai_utilities import AsyncAiClient, AiSettings
    settings = AiSettings(api_key="test-key", model="test-model")
    return AsyncAiClient(settings, provider=fake_async_provider)
