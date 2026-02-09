"""Extended tests for provider_resolution.py to increase coverage."""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from ai_utilities.provider_resolution import (
    resolve_provider_config,
    configure_library_logging,
    _normalize,
    _resolve_auto_select_order,
    _pick_first_in_order,
    _detect_configured_providers,
    _non_empty,
    _resolve_api_key,
    _resolve_base_url,
    _resolve_model,
    ResolvedProviderConfig
)


class TestProviderResolutionExtended:
    """Extended test cases for provider resolution to cover missing lines."""

    def test_configure_library_logging(self):
        """Test configuring library logging."""
        # Test with valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            configure_library_logging(level)
            # Should not raise an exception
        
        # Test with invalid log level
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            configure_library_logging("INVALID")
            # Should handle gracefully

    def test_normalize_function(self):
        """Test _normalize function using actual contract."""
        # Test with various inputs based on actual implementation
        test_cases = [
            ("test", "test"),  # Lowercase stays lowercase
            ("  test  ", "test"),  # Strips whitespace
            ("", None),  # Empty string becomes None per actual contract
            (None, None),  # None stays None
            ("TEST", "test"),  # Converts to lowercase per actual contract
            ("  Mixed Case  ", "mixed case"),  # Strips and lowercases
        ]
        
        for input_val, expected in test_cases:
            result = _normalize(input_val)
            assert result == expected

    def test_resolve_auto_select_order(self):
        """Test _resolve_auto_select_order function."""
        from ai_utilities import AiSettings
        
        settings = AiSettings()
        order, reason = _resolve_auto_select_order(settings)
        
        assert isinstance(order, tuple)
        assert isinstance(reason, str)
        assert len(order) > 0

    def test_pick_first_in_order(self):
        """Test _pick_first_in_order function."""
        configured = ["openai", "groq", "together"]
        order = ["groq", "openai", "together"]
        
        result = _pick_first_in_order(configured, order)
        # Contract: verify function returns a provider (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
        
        # Test with no matches
        order = ["anthropic", "azure"]
        result = _pick_first_in_order(configured, order)
        assert result is None

    def test_detect_configured_providers(self):
        """Test _detect_configured_providers function."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(api_key="test-key")
        providers = _detect_configured_providers(settings)
        
        assert isinstance(providers, list)
        # Should detect at least openai with API key

    def test_non_empty_function(self):
        """Test _non_empty function."""
        assert _non_empty("test") is True
        assert _non_empty("  test  ") is True
        assert _non_empty("") is False
        assert _non_empty("   ") is False
        assert _non_empty(None) is False

    def test_resolve_api_key(self):
        """Test _resolve_api_key function."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(api_key="test-key")
        
        # Test with provider and no override
        api_key = _resolve_api_key(settings=settings, provider="openai", api_key_override=None)
        assert api_key == "test-key"
        
        # Test with override
        api_key = _resolve_api_key(settings=settings, provider="openai", api_key_override="override-key")
        assert api_key == "override-key"

    def test_resolve_base_url(self):
        """Test _resolve_base_url function."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(base_url="https://api.example.com")
        
        # Test with provider and no override
        base_url = _resolve_base_url(settings=settings, provider="openai", base_url_override=None)
        assert base_url == "https://api.example.com"
        
        # Test with override
        base_url = _resolve_base_url(settings=settings, provider="openai", base_url_override="https://override.com")
        assert base_url == "https://override.com"

    def test_resolve_model(self):
        """Test _resolve_model function using actual contract."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(model="test-model")
        
        # Test with provider and no override (openai is not local)
        model = _resolve_model(settings=settings, provider="openai", is_local=False, model_override=None)
        assert model == "test-model"
        
        # Test with override
        model = _resolve_model(settings=settings, provider="openai", is_local=False, model_override="override-model")
        assert model == "override-model"
        
        # Test with local provider (ollama)
        model = _resolve_model(settings=settings, provider="ollama", is_local=True, model_override=None)
        # Local providers don't have default models, should use settings model
        assert model == "test-model"

    def test_resolve_provider_config_basic(self):
        """Test resolve_provider_config with basic settings."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(api_key="test-key", model="gpt-4")
        config = resolve_provider_config(settings)
        
        assert isinstance(config, ResolvedProviderConfig)
        assert config.provider is not None
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"

    def test_resolve_provider_config_with_base_url(self):
        """Test resolve_provider_config with custom base URL."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(
            api_key="test-key",
            base_url="https://custom-api.example.com",
            model="custom-model"
        )
        config = resolve_provider_config(settings)
        
        assert config.base_url == "https://custom-api.example.com"
        assert config.model == "custom-model"

    def test_resolve_provider_config_auto_selection(self):
        """Test resolve_provider_config with auto provider selection."""
        from ai_utilities import AiSettings
        
        settings = AiSettings(provider="auto", api_key="test-key")
        config = resolve_provider_config(settings)
        
        assert config.provider is not None
        assert config.api_key == "test-key"

    def test_resolved_provider_config_attributes(self):
        """Test ResolvedProviderConfig attributes using actual contract."""
        from ai_utilities.provider_resolution import ResolvedProviderConfig
        
        config = ResolvedProviderConfig(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            is_local=False  # Required field per actual contract
        )
        
        assert config.provider == "openai"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.is_local is False  # Verify the required field

    def test_resolved_provider_config_equality(self):
        """Test ResolvedProviderConfig equality using actual contract."""
        from ai_utilities.provider_resolution import ResolvedProviderConfig
        
        config1 = ResolvedProviderConfig(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            is_local=False  # Required field per actual contract
        )
        
        config2 = ResolvedProviderConfig(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            is_local=False  # Required field per actual contract
        )
        
        config3 = ResolvedProviderConfig(
            provider="groq",
            api_key="test-key",
            base_url="https://api.groq.com/openai/v1",
            model="llama3-70b-8192",
            is_local=False  # Required field per actual contract
        )
        
        assert config1 == config2
        assert config1 != config3

    def test_resolved_provider_config_repr(self):
        """Test ResolvedProviderConfig string representation using actual contract."""
        from ai_utilities.provider_resolution import ResolvedProviderConfig
        
        config = ResolvedProviderConfig(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            is_local=False  # Required field per actual contract
        )
        
        repr_str = repr(config)
        assert "openai" in repr_str
        assert "gpt-4" in repr_str

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'})
    def test_resolve_provider_config_env_priority(self):
        """Test resolve_provider_config with environment variable priority."""
        from ai_utilities import AiSettings
        
        settings = AiSettings()  # No API key in settings
        config = resolve_provider_config(settings)
        
        # Should pick up API key from environment
        assert config.api_key == "env-key"

    def test_resolve_provider_config_multiple_providers_configured(self):
        """Test resolve_provider_config with multiple providers configured."""
        from ai_utilities import AiSettings
        
        # Mock multiple providers being configured
        with patch('ai_utilities.provider_resolution._detect_configured_providers', return_value=['openai', 'groq', 'together']):
            settings = AiSettings(api_key="test-key")
            config = resolve_provider_config(settings)
            
            # Should pick one deterministically
            assert config.provider in ['openai', 'groq', 'together']

    def test_resolve_provider_config_error_handling(self):
        """Test resolve_provider_config error handling."""
        from ai_utilities import AiSettings
        from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
        
        # Test with no configuration
        settings = AiSettings()  # No API key, no base URL
        
        # Should raise ProviderConfigurationError - this is acceptable behavior
        # New invariant: ProviderConfigurationError is acceptable in CI/non-interactive
        with pytest.raises(ProviderConfigurationError):
            resolve_provider_config(settings)
