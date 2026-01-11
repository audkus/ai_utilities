"""Tests for the new model resolution functionality."""

import os
import pytest
from unittest.mock import patch

from ai_utilities.config_resolver import resolve_model, MissingModelError
from ai_utilities.config_models import AiSettings
from ai_utilities.client import AiClient
from ai_utilities.providers.provider_exceptions import ProviderConfigurationError


class TestResolveModel:
    """Test the resolve_model function."""

    def test_settings_model_takes_priority(self):
        """Test that settings.model takes priority over everything else."""
        settings = AiSettings(model="gpt-4")
        model = resolve_model(settings, "openai")
        assert model == "gpt-4"

    def test_environment_variable_fallback(self):
        """Test that AI_MODEL environment variable is used when settings.model is None."""
        with patch.dict(os.environ, {"AI_MODEL": "gpt-3.5-turbo"}):
            settings = AiSettings()  # No model in settings
            model = resolve_model(settings, "openai")
            assert model == "gpt-3.5-turbo"

    def test_provider_defaults(self):
        """Test that provider-specific defaults are used."""
        settings = AiSettings()  # No model in settings
        
        # Test providers with defaults
        assert resolve_model(settings, "openai") == "gpt-3.5-turbo"
        assert resolve_model(settings, "groq") == "llama3-70b-8192"
        assert resolve_model(settings, "together") == "meta-llama/Llama-3-8b-chat-hf"
        assert resolve_model(settings, "openrouter") == "meta-llama/llama-3-8b-instruct:free"

    def test_missing_model_error(self):
        """Test that MissingModelError is raised for providers without defaults."""
        settings = AiSettings()  # No model in settings
        
        with pytest.raises(MissingModelError) as exc_info:
            resolve_model(settings, "ollama")
        
        assert "Model is required for provider 'ollama'" in str(exc_info.value)
        assert "AiSettings(model=...)" in str(exc_info.value)
        assert "AI_MODEL=..." in str(exc_info.value)

    def test_empty_model_values_ignored(self):
        """Test that empty/whitespace model values are ignored."""
        # Test empty string
        settings = AiSettings(model="")
        with patch.dict(os.environ, {"AI_MODEL": "gpt-4"}):
            model = resolve_model(settings, "openai")
            assert model == "gpt-4"
        
        # Test whitespace only
        settings = AiSettings(model="   ")
        with patch.dict(os.environ, {"AI_MODEL": "gpt-3.5-turbo"}):
            model = resolve_model(settings, "openai")
            assert model == "gpt-3.5-turbo"

    def test_model_is_stripped(self):
        """Test that model values are stripped of whitespace."""
        settings = AiSettings(model="  gpt-4  ")
        model = resolve_model(settings, "openai")
        assert model == "gpt-4"
        
        with patch.dict(os.environ, {"AI_MODEL": "  gpt-3.5-turbo  "}):
            settings = AiSettings()
            model = resolve_model(settings, "openai")
            assert model == "gpt-3.5-turbo"


class TestAiClientModelRequirement:
    """Test that AiClient requires model configuration."""

    def test_explicit_model_works(self):
        """Test that providing model explicitly works."""
        client = AiSettings(api_key="test-key", model="gpt-4")
        assert client.model == "gpt-4"

    def test_environment_model_works(self):
        """Test that AI_MODEL environment variable works."""
        with patch.dict(os.environ, {"AI_API_KEY": "test-key", "AI_MODEL": "gpt-3.5-turbo"}):
            client = AiClient()
            assert client.settings.model is None  # Still None in settings
            # But resolve_model will find it
            from ai_utilities.config_resolver import resolve_model
            model = resolve_model(client.settings, client.settings.provider or "openai")
            assert model == "gpt-3.5-turbo"

    def test_missing_model_raises_error(self):
        """Test that missing model raises ProviderConfigurationError."""
        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            # Remove AI_MODEL if it exists
            env = dict(os.environ)
            env.pop("AI_MODEL", None)
            
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ProviderConfigurationError) as exc_info:
                    AiClient()
                
                assert "Model is required" in str(exc_info.value)

    def test_local_provider_requires_explicit_model(self):
        """Test that local providers like ollama require explicit model."""
        with patch.dict(os.environ, {"AI_API_KEY": "test-key", "AI_PROVIDER": "ollama"}):
            with pytest.raises(ProviderConfigurationError) as exc_info:
                AiClient()
            
            assert "ollama" in str(exc_info.value)
            assert "Model is required" in str(exc_info.value)

    def test_cloud_provider_has_defaults(self):
        """Test that cloud providers have sensible defaults."""
        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            # This should work with OpenAI's default
            client = AiClient()
            from ai_utilities.config_resolver import resolve_model
            model = resolve_model(client.settings, "openai")
            assert model == "gpt-3.5-turbo"


@pytest.fixture
def test_settings():
    """Fixture providing test settings with explicit model."""
    return AiSettings(
        provider="openai",
        api_key="test-key",
        model="unit-test-model"
    )


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_create_client_requires_model(self):
        """Test that create_client now requires model parameter."""
        # Should fail without model
        with pytest.raises(ProviderConfigurationError):
            from ai_utilities.client import create_client
            create_client(api_key="test-key")
        
        # Should work with model
        from ai_utilities.client import create_client
        client = create_client(api_key="test-key", model="gpt-4")
        assert client.settings.model == "gpt-4"

    def test_settings_model_can_be_none(self):
        """Test that AiSettings.model can be None (for environment resolution)."""
        settings = AiSettings(api_key="test-key")  # No model
        assert settings.model is None
        
        # But resolve_model should find it from environment
        with patch.dict(os.environ, {"AI_MODEL": "gpt-3.5-turbo"}):
            from ai_utilities.config_resolver import resolve_model
            model = resolve_model(settings, "openai")
            assert model == "gpt-3.5-turbo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
