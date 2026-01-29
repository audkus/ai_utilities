"""Tests for configuration resolver."""

import os
import pytest
from unittest.mock import patch

from ai_utilities.config_resolver import (
    resolve_request_config,
    resolve_provider,
    resolve_api_key,
    resolve_base_url,
    ResolvedConfig,
    UnknownProviderError,
    MissingApiKeyError
)
from ai_utilities.client import AiSettings


class TestProviderResolution:
    """Test provider resolution logic."""
    
    def test_resolve_provider_per_request(self):
        """Test per-request provider wins."""
        result = resolve_provider(provider="groq")
        assert result == "groq"
    
    def test_resolve_provider_env_override(self):
        """Test environment provider override."""
        result = resolve_provider(env_provider="together")
        assert result == "together"
    
    def test_resolve_provider_from_url_ollama(self):
        """Test provider inference from Ollama URL."""
        result = resolve_provider(base_url="http://localhost:11434/v1")
        assert result == "ollama"
    
    def test_resolve_provider_from_url_lmstudio(self):
        """Test provider inference from LM Studio URL."""
        result = resolve_provider(base_url="http://localhost:1234/v1")
        assert result == "lmstudio"
    
    def test_resolve_provider_from_url_openai(self):
        """Test provider inference from OpenAI URL."""
        result = resolve_provider(base_url="https://api.openai.com/v1")
        assert result == "openai"
    
    def test_resolve_provider_default(self):
        """Test default provider is OpenAI."""
        # Clear any environment variables that might interfere
        import os
        env_vars_to_clear = [
            'AI_PROVIDER', 'TEXT_GENERATION_WEBUI_BASE_URL', 'FASTCHAT_BASE_URL', 
            'OLLAMA_BASE_URL', 'LMSTUDIO_BASE_URL'
        ]
        original_values = {}
        for var in env_vars_to_clear:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        try:
            result = resolve_provider(env_provider=None)
            assert result == "openai"
        finally:
            # Restore environment
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value


class TestApiKeyResolution:
    """Test API key resolution logic."""
    
    def test_resolve_api_key_per_request(self):
        """Test per-request API key wins."""
        result = resolve_api_key("openai", api_key="sk-test-key")
        assert result == "sk-test-key"
    
    def test_resolve_api_key_settings_override(self):
        """Test settings API_KEY override."""
        result = resolve_api_key("openai", settings_api_key="sk-settings-key")
        assert result == "sk-settings-key"
    
    def test_resolve_api_key_vendor_specific(self):
        """Test vendor-specific API key from environment."""
        env_vars = {"OPENAI_API_KEY": "sk-openai-key"}
        result = resolve_api_key("openai", env_vars=env_vars)
        assert result == "sk-openai-key"
    
    def test_resolve_api_key_from_settings(self):
        """Test vendor-specific API key from AiSettings."""
        settings = AiSettings()
        settings.openai_api_key = "sk-settings-openai"
        
        result = resolve_api_key("openai", settings=settings)
        assert result == "sk-settings-openai"
    
    def test_resolve_api_key_local_fallback(self):
        """Test fallback tokens for local providers."""
        result = resolve_api_key("ollama")
        assert result == "ollama"
        
        result = resolve_api_key("lmstudio")
        assert result == "lm-studio"
    
    def test_resolve_api_key_missing_cloud(self):
        """Test missing API key for cloud provider raises error."""
        with pytest.raises(MissingApiKeyError) as exc_info:
            resolve_api_key("openai")
        
        assert "API key is required" in str(exc_info.value)


class TestBaseUrlResolution:
    """Test base URL resolution logic."""
    
    def test_resolve_base_url_per_request(self):
        """Test per-request base URL wins."""
        result = resolve_base_url("openai", base_url="http://custom:8080/v1")
        assert result == "http://custom:8080/v1"
    
    def test_resolve_base_url_settings_override(self):
        """Test settings base URL override."""
        result = resolve_base_url("openai", settings_base_url="http://settings:8080/v1")
        assert result == "http://settings:8080/v1"
    
    def test_resolve_base_url_provider_defaults(self):
        """Test provider default base URLs."""
        assert resolve_base_url("openai") == "https://api.openai.com/v1"
        assert resolve_base_url("groq") == "https://api.groq.com/openai/v1"
        assert resolve_base_url("ollama") == "http://localhost:11434/v1"
        assert resolve_base_url("lmstudio") == "http://localhost:1234/v1"


class TestResolvedConfig:
    """Test complete configuration resolution."""
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-env-openai-key',
        'AI_PROVIDER': 'groq'
    }, clear=True)
    def test_resolve_request_config_full(self):
        """Test complete request configuration resolution."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        settings.openai_api_key = "sk-settings-openai"
        settings.base_url = None  # Clear environment-derived base URL
        
        config = resolve_request_config(
            settings,
            provider="openai",  # Should override env provider
            api_key="sk-request-key",  # Should override all
            model="gpt-4",
            temperature=0.5
        )
        
        assert isinstance(config, ResolvedConfig)
        assert config.provider == "openai"
        assert config.api_key == "sk-request-key"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
    
    @patch.dict(os.environ, {
        'GROQ_API_KEY': 'gsk-env-groq-key',
        'AI_PROVIDER': 'groq'
    }, clear=True)
    def test_resolve_request_config_env_provider(self):
        """Test configuration using environment provider."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        config = resolve_request_config(settings)
        
        assert config.provider == "groq"
        assert config.api_key == "gsk-env-groq-key"
        assert config.base_url == "https://api.groq.com/openai/v1"
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-env-openai-key'
    }, clear=True)
    def test_resolve_request_config_vendor_key(self):
        """Test configuration using vendor-specific key."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        config = resolve_request_config(settings)
        
        # Should infer OpenAI from default and use vendor key
        assert config.provider == "openai"
        assert config.api_key == "sk-env-openai-key"
    
    @patch.dict(os.environ, {
        'LMSTUDIO_BASE_URL': 'http://localhost:1234/v1',
        'LMSTUDIO_MODEL': 'local-model'
    }, clear=True)
    def test_resolve_request_config_local_provider_inference(self):
        """Test local provider inference from base URL."""
        settings = AiSettings(_env_file=None, provider=None)  # Don't load from .env, no explicit provider
        settings.provider = None  # Explicitly clear provider to force inference
        
        config = resolve_request_config(settings)
        
        assert config.provider == "lmstudio"
        assert config.base_url == "http://localhost:1234/v1"
        assert config.api_key == "lm-studio"  # Fallback token
    
    @patch.dict(os.environ, {}, clear=True)
    def test_resolve_request_config_with_settings_vendor_keys(self):
        """Test configuration using vendor keys from settings."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        settings.groq_api_key = "gsk-settings-groq"
        
        config = resolve_request_config(settings, provider="groq")
        
        assert config.provider == "groq"
        assert config.api_key == "gsk-settings-groq"
        assert config.base_url == "https://api.groq.com/openai/v1"
    
    def test_resolve_request_config_precedence(self):
        """Test proper precedence order."""
        # Set up environment
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-env-key',
            'AI_API_KEY': 'sk-generic-env-key',
            'AI_BASE_URL': 'http://env-url:8080/v1'
        }, clear=True):
            settings = AiSettings(_env_file=None)  # Don't load from .env
            settings.openai_api_key = "sk-settings-key"
            settings.api_key = "sk-settings-generic"
            settings.base_url = "http://settings-url:8080/v1"
            
            # Test 1: Per-request overrides everything
            config = resolve_request_config(
                settings,
                api_key="sk-request-key",
                base_url="http://request-url:8080/v1"
            )
            assert config.api_key == "sk-request-key"
            assert config.base_url == "http://request-url:8080/v1"
            
            # Test 2: Settings override environment
            config = resolve_request_config(settings)
            # Provider-specific keys win over generic AI_API_KEY
            assert config.api_key == "sk-settings-key"
            assert config.base_url == "http://settings-url:8080/v1"
            
            # Test 3: Environment vendor key used when no settings override
            settings.api_key = None
            config = resolve_request_config(settings, provider="openai")
            assert config.api_key == "sk-settings-key"  # Vendor key from settings


class TestErrorHandling:
    """Test error handling in configuration resolution."""
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all env vars
    def test_unknown_provider_error(self):
        """Test unknown provider raises ProviderConfigurationError."""
        # Unknown providers should be treated as cloud providers and require API keys
        from ai_utilities.providers.provider_factory import create_provider
        from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
        
        # Create settings with invalid provider - this should fail at pydantic validation
        # But let's test the resolver directly instead
        from ai_utilities.config_resolver import resolve_request_config, UnknownProviderError
        
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        with pytest.raises(UnknownProviderError) as exc_info:
            resolve_request_config(settings, provider="invalid-provider")
        
        assert "Unknown provider: invalid-provider" in str(exc_info.value)
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all env vars
    def test_missing_api_key_cloud_provider(self):
        """Test MissingApiKeyError for cloud provider without key."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        with pytest.raises(MissingApiKeyError) as exc_info:
            resolve_request_config(settings, provider="openai")
        
        assert "API key is required" in str(exc_info.value)
    
    @patch.dict(os.environ, {}, clear=True)  # Clear all env vars
    def test_local_provider_no_key_required(self):
        """Test local providers don't require API keys."""
        with patch.dict(
            os.environ,
            {
                "OLLAMA_BASE_URL": "http://localhost:11434/v1",
                "OLLAMA_MODEL": "local-model",
            },
            clear=True,
        ):
            settings = AiSettings(_env_file=None)
            config = resolve_request_config(settings)

            assert config.provider == "ollama"
            assert config.api_key == "ollama"  # Fallback token


class TestProviderSpecific:
    """Test provider-specific configuration."""
    
    @patch.dict(os.environ, {'TOGETHER_API_KEY': 'tgp-together-key'}, clear=True)
    def test_together_ai_config(self):
        """Test Together AI configuration."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        config = resolve_request_config(settings, provider="together")
        
        assert config.provider == "together"
        assert config.api_key == "tgp-together-key"
        assert config.base_url == "https://api.together.xyz/v1"
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'sk-or-openrouter-key'}, clear=True)
    def test_openrouter_config(self):
        """Test OpenRouter configuration."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        config = resolve_request_config(settings, provider="openrouter")
        
        assert config.provider == "openrouter"
        assert config.api_key == "sk-or-openrouter-key"
        assert config.base_url == "https://openrouter.ai/api/v1"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""
    
    @patch.dict(os.environ, {'AI_API_KEY': 'sk-legacy-key'}, clear=True)
    def test_legacy_ai_api_key(self):
        """Test AI_API_KEY still works as generic override."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        
        config = resolve_request_config(settings, provider="openai")
        
        assert config.api_key == "sk-legacy-key"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_settings_still_work(self):
        """Test that default AiSettings still work."""
        settings = AiSettings(_env_file=None)  # Don't load from .env
        settings.openai_api_key = "sk-test-key"
        
        config = resolve_request_config(settings)
        
        # Should infer openai as default and use the key
        assert config.provider == "openai"
        assert config.api_key == "sk-test-key"
