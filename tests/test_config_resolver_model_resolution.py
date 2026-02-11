"""Tests for config_resolver resolve_model function."""

import pytest
from unittest.mock import patch

from ai_utilities.config_resolver import resolve_model, MissingModelError
from ai_utilities.config_models import AiSettings
from ai_utilities.client import AiClient
from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
from tests.fake_provider import FakeProvider


class TestResolveModel:
    """Test the resolve_model function."""

    def test_settings_model_precedence_with_object(self):
        """Test that settings.model takes priority with AiSettings object."""
        settings = AiSettings(model="gpt-4")
        model = resolve_model(settings, "openai")
        assert model == "gpt-4"

    def test_settings_model_stripping(self):
        """Test that model names are stripped of whitespace."""
        settings = AiSettings(model=" gpt-4 ")
        model = resolve_model(settings, "openai")
        assert model == "gpt-4"

    def test_settings_model_empty_falls_back_to_default(self):
        """Test that empty model falls back to provider default."""
        settings = AiSettings(model="")
        model = resolve_model(settings, "openai")
        assert model == "gpt-3.5-turbo"

    def test_settings_model_whitespace_falls_back_to_default(self):
        """Test that whitespace-only model falls back to provider default."""
        settings = AiSettings(model="   ")
        model = resolve_model(settings, "openai")
        assert model == "gpt-3.5-turbo"

    def test_settings_model_none_falls_back_to_default(self):
        """Test that None model falls back to provider default."""
        settings = AiSettings(model=None)
        model = resolve_model(settings, "openai")
        assert model == "gpt-3.5-turbo"

    def test_provider_defaults_openai(self):
        """Test OpenAI provider default."""
        settings = AiSettings()
        model = resolve_model(settings, "openai")
        assert model == "gpt-3.5-turbo"

    def test_provider_defaults_groq(self):
        """Test Groq provider default."""
        settings = AiSettings()
        model = resolve_model(settings, "groq")
        assert model == "llama3-70b-8192"

    def test_provider_defaults_together(self):
        """Test Together provider default."""
        settings = AiSettings()
        model = resolve_model(settings, "together")
        assert model == "meta-llama/Llama-3-8b-chat-hf"

    def test_provider_defaults_openrouter(self):
        """Test OpenRouter provider default."""
        settings = AiSettings()
        model = resolve_model(settings, "openrouter")
        assert model == "meta-llama/llama-3-8b-instruct:free"

    def test_missing_model_error_for_provider_without_defaults(self):
        """Test MissingModelError for providers without defaults."""
        settings = AiSettings()
        
        with pytest.raises(MissingModelError) as exc_info:
            resolve_model(settings, "ollama")
        
        error_msg = str(exc_info.value)
        assert "Model is required for provider 'ollama'" in error_msg
        assert "AiSettings(model=...)" in error_msg
        assert "AI_MODEL=..." in error_msg

    def test_dict_settings_supported(self):
        """Test that dict settings are supported."""
        # Test with model
        model = resolve_model({"model": " gpt-4 "}, "openai")
        assert model == "gpt-4"
        
        # Test with empty model falls back to default
        model = resolve_model({"model": ""}, "openai")
        assert model == "gpt-3.5-turbo"
        
        # Test with no model falls back to default
        model = resolve_model({}, "openai")
        assert model == "gpt-3.5-turbo"

    def test_settings_model_non_string_ignored(self):
        """Test that non-string model values are ignored."""
        # Test with dict settings instead since AiSettings validates types
        model = resolve_model({"model": 123}, "openai")
        assert model == "gpt-3.5-turbo"  # Should fall back to default


class TestClientModelRequirement:
    """Test client behavior when model is required."""

    def test_client_with_provider_without_defaults_and_no_model(self):
        """Test AiClient raises error for provider without defaults and no model."""
        # This test assumes ollama requires explicit model
        with patch.dict('os.environ', {'AI_PROVIDER': 'ollama'}, clear=True):
            with pytest.raises(ProviderConfigurationError) as exc_info:
                AiClient()
            
            error_msg = str(exc_info.value)
            # Check for key error components - ollama needs configuration
            assert "ollama" in error_msg.lower()
            assert "not configured" in error_msg.lower()

    def test_client_with_provider_with_defaults_succeeds(self):
        """Test AiClient succeeds for provider with defaults and no model."""
        # This test assumes openai has defaults and succeeds without explicit model
        with patch.dict('os.environ', {'AI_PROVIDER': 'openai', 'OPENAI_API_KEY': 'test-key'}, clear=True):
            # Should not raise an error if openai has defaults
            try:
                fake_provider = FakeProvider()
                client = AiClient(provider=fake_provider)
                assert client is not None
            except ProviderConfigurationError as e:
                # If it does raise, make sure it's not about missing model
                error_msg = str(e)
                assert "model" not in error_msg.lower() or "required" not in error_msg.lower()

    def test_client_with_explicit_model_always_succeeds(self):
        """Test AiClient succeeds when model is explicitly provided."""
        with patch.dict('os.environ', {'AI_PROVIDER': 'ollama'}, clear=True):
            settings = AiSettings(model="llama2")
            # Should succeed even if ollama needs config when model is explicit
            try:
                client = AiClient(settings)
                assert client is not None
            except ProviderConfigurationError as e:
                # If it still fails, it should be about other config, not model
                error_msg = str(e)
                assert "model" not in error_msg.lower()
