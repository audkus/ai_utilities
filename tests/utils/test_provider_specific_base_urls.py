"""Tests for provider-specific base URL support.

These tests verify that provider-specific base URL environment variables
(TEXT_GENERATION_WEBUI_BASE_URL, FASTCHAT_BASE_URL, etc.) work correctly
in the core configuration system.
"""

import os
import pytest
from unittest.mock import patch

from ai_utilities.config_resolver import (
    resolve_provider,
    resolve_base_url,
    _get_provider_specific_base_url,
    _infer_provider_from_env_base_urls,
)
from ai_utilities.client import AiClient
from ai_utilities.config_models import AiSettings


class TestProviderSpecificBaseUrls:
    """Test provider-specific base URL functionality."""

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_infers_provider_from_text_generation_webui_base_url(self):
        """Test that provider is inferred from TEXT_GENERATION_WEBUI_BASE_URL."""
        provider = resolve_provider()
        assert provider == "text-generation-webui"

    @patch.dict(os.environ, {
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
    })
    def test_infers_provider_from_fastchat_base_url(self):
        """Test that provider is inferred from FASTCHAT_BASE_URL."""
        provider = resolve_provider()
        assert provider == "fastchat"

    @patch.dict(os.environ, {
        "OLLAMA_BASE_URL": "http://localhost:11434/v1"
    })
    def test_infers_provider_from_ollama_base_url(self):
        """Test that provider is inferred from OLLAMA_BASE_URL."""
        provider = resolve_provider()
        assert provider == "ollama"

    @patch.dict(os.environ, {
        "LMSTUDIO_BASE_URL": "http://localhost:1234/v1"
    })
    def test_infers_provider_from_lmstudio_base_url(self):
        """Test that provider is inferred from LMSTUDIO_BASE_URL."""
        provider = resolve_provider()
        assert provider == "lmstudio"

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1",
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
    })
    def test_prioritizes_first_provider_base_url_found(self):
        """Test that the first provider base URL found is used."""
        provider = resolve_provider()
        # Should be text-generation-webui (first in mapping)
        assert provider == "text-generation-webui"

    @patch.dict(os.environ, {
        "AI_PROVIDER": "openai",
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_explicit_provider_overrides_env_base_url(self):
        """Test that explicit AI_PROVIDER takes precedence."""
        provider = resolve_provider(env_provider=os.getenv("AI_PROVIDER"))
        assert provider == "openai"

    @patch.dict(os.environ, {
        "AI_BASE_URL": "http://custom-endpoint.com/v1",
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_explicit_base_url_overrides_provider_specific(self):
        """Test that explicit base_url parameter takes precedence."""
        provider = resolve_provider()
        base_url = resolve_base_url(provider, base_url="http://custom-endpoint.com/v1")
        assert base_url == "http://custom-endpoint.com/v1"

    def test_no_provider_base_urls_returns_default(self):
        """Test that default provider is returned when no provider-specific URLs exist."""
        with patch.dict(os.environ, {}, clear=True):
            provider = resolve_provider()
            assert provider == "openai"


class TestBaseUrlResolution:
    """Test base URL resolution with provider-specific environment variables."""

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_resolves_text_generation_webui_base_url(self):
        """Test that TEXT_GENERATION_WEBUI_BASE_URL is used for text-generation-webui provider."""
        base_url = resolve_base_url("text-generation-webui")
        assert base_url == "http://localhost:5000/v1"

    @patch.dict(os.environ, {
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
    })
    def test_resolves_fastchat_base_url(self):
        """Test that FASTCHAT_BASE_URL is used for fastchat provider."""
        base_url = resolve_base_url("fastchat")
        assert base_url == "http://localhost:8000/v1"

    @patch.dict(os.environ, {
        "OLLAMA_BASE_URL": "http://localhost:11434/v1"
    })
    def test_resolves_ollama_base_url(self):
        """Test that OLLAMA_BASE_URL is used for ollama provider."""
        base_url = resolve_base_url("ollama")
        assert base_url == "http://localhost:11434/v1"

    @patch.dict(os.environ, {
        "LMSTUDIO_BASE_URL": "http://localhost:1234/v1"
    })
    def test_resolves_lmstudio_base_url(self):
        """Test that LMSTUDIO_BASE_URL is used for lmstudio provider."""
        base_url = resolve_base_url("lmstudio")
        assert base_url == "http://localhost:1234/v1"

    @patch.dict(os.environ, {
        "AI_BASE_URL": "http://custom-endpoint.com/v1",
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_ai_base_url_takes_precedence(self):
        """Test that AI_BASE_URL takes precedence over provider-specific URLs."""
        base_url = resolve_base_url("text-generation-webui", settings_base_url="http://custom-endpoint.com/v1")
        assert base_url == "http://custom-endpoint.com/v1"

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_per_request_base_url_takes_precedence(self):
        """Test that per-request base_url takes highest precedence."""
        base_url = resolve_base_url(
            "text-generation-webui", 
            base_url="http://per-request.com/v1",
            settings_base_url="http://settings.com/v1"
        )
        assert base_url == "http://per-request.com/v1"

    def test_unknown_provider_returns_none(self):
        """Test that unknown provider returns None for provider-specific base URL."""
        base_url = _get_provider_specific_base_url("unknown_provider")
        assert base_url is None


class TestClientIntegration:
    """Test that AiClient works correctly with provider-specific base URLs."""

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1",
        "AI_API_KEY": "test-key"
    })
    def test_client_uses_text_generation_webui_base_url(self):
        """Test that AiClient uses TEXT_GENERATION_WEBUI_BASE_URL when provider is set."""
        settings = AiSettings(provider="text-generation-webui")  # Explicitly set provider
        client = AiClient(settings=settings)  # Pass explicit settings
        # Should use text-generation-webui provider and resolve its base URL
        assert client.settings.provider == "text-generation-webui"
        assert client.settings.base_url == "http://localhost:5000/v1"

    @patch.dict(os.environ, {
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1",
        "AI_API_KEY": "test-key"
    })
    def test_client_uses_fastchat_base_url(self):
        """Test that AiClient uses FASTCHAT_BASE_URL when provider is set."""
        settings = AiSettings(provider="fastchat")  # Explicitly set provider
        client = AiClient(settings=settings)  # Pass explicit settings
        assert client.settings.provider == "fastchat"
        assert client.settings.base_url == "http://localhost:8000/v1"

    @patch.dict(os.environ, {
        "AI_PROVIDER": "openai",
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1",
        "AI_API_KEY": "test-key"
    })
    def test_explicit_provider_overrides_base_url_inference(self):
        """Test that explicit AI_PROVIDER prevents base URL inference."""
        settings = AiSettings()  # Create settings with patched environment
        client = AiClient(settings=settings)  # Pass explicit settings
        assert client.settings.provider == "openai"
        # Should use OpenAI default, not the text-generation-webui URL
        assert client.settings.base_url == "https://api.openai.com/v1"

    @patch.dict(os.environ, {
        "AI_BASE_URL": "http://custom.com/v1",
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1",
        "AI_API_KEY": "test-key"
    })
    def test_ai_base_url_overrides_provider_specific(self):
        """Test that AI_BASE_URL overrides provider-specific inference."""
        settings = AiSettings()  # Create settings with patched environment
        client = AiClient(settings=settings)  # Pass explicit settings
        assert client.settings.base_url == "http://custom.com/v1"

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
    })
    def test_provider_base_url_without_api_key_works(self):
        """Test that provider-specific base URL works without API key."""
        settings = AiSettings(provider="text-generation-webui")  # Explicitly set provider
        client = AiClient(settings=settings)  # Pass explicit settings
        assert client.settings.provider == "text-generation-webui"
        assert client.settings.base_url == "http://localhost:5000/v1"
        assert client.settings.api_key is None  # Local providers don't need API keys


class TestEnvironmentHelperFunctions:
    """Test the helper functions for provider-specific base URL detection."""

    def test_get_provider_specific_base_url(self):
        """Test _get_provider_specific_base_url function."""
        with patch.dict(os.environ, {
            "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
        }):
            base_url = _get_provider_specific_base_url("text-generation-webui")
            assert base_url == "http://localhost:5000/v1"

            base_url = _get_provider_specific_base_url("fastchat")
            assert base_url is None

    def test_infer_provider_from_env_base_urls(self):
        """Test _infer_provider_from_env_base_urls function."""
        with patch.dict(os.environ, {
            "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
        }):
            provider = _infer_provider_from_env_base_urls()
            assert provider == "fastchat"

        with patch.dict(os.environ, {}, clear=True):
            provider = _infer_provider_from_env_base_urls()
            assert provider is None

    def test_provider_name_variations(self):
        """Test that provider name variations work correctly."""
        with patch.dict(os.environ, {
            "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1"
        }):
            # Test both naming variations
            base_url1 = _get_provider_specific_base_url("text_generation_webui")
            base_url2 = _get_provider_specific_base_url("text-generation-webui")
            
            assert base_url1 == "http://localhost:5000/v1"
            assert base_url2 == "http://localhost:5000/v1"


class TestPrecedenceOrder:
    """Test the precedence order of base URL resolution."""

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": "http://localhost:5000/v1",
        "AI_BASE_URL": "http://ai-base-url.com/v1"
    })
    def test_base_url_precedence_order(self):
        """Test the complete precedence order:
        1. Per-request base_url (highest)
        2. Settings base_url (AI_BASE_URL)
        3. Provider-specific base URL
        4. Provider default (lowest)
        """
        # 1. Per-request should win
        base_url = resolve_base_url(
            "text-generation-webui",
            base_url="http://per-request.com/v1",
            settings_base_url="http://ai-base-url.com/v1"
        )
        assert base_url == "http://per-request.com/v1"

        # 2. Settings should beat provider-specific
        base_url = resolve_base_url(
            "text-generation-webui",
            settings_base_url="http://ai-base-url.com/v1"
        )
        assert base_url == "http://ai-base-url.com/v1"

        # 3. Provider-specific should beat default
        base_url = resolve_base_url("text-generation-webui")
        assert base_url == "http://localhost:5000/v1"

        # 4. Default should be used when nothing else is available
        with patch.dict(os.environ, {}, clear=True):
            base_url = resolve_base_url("openai")
            assert base_url == "https://api.openai.com/v1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
