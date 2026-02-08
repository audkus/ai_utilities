"""Tests for provider-specific base URL support.

These tests verify that provider-specific base URL environment variables
(TEXT_GENERATION_WEBUI_BASE_URL, FASTCHAT_BASE_URL, etc.) work correctly
in the core configuration system.
"""

import os
import pytest
from unittest.mock import patch

from ai_utilities.config_resolver import (
    resolve_base_url,
    resolve_provider,
)
from ai_utilities.client import AiClient
from ai_utilities.config_models import AiSettings


def get_actual_tgwui_url():
    """Get the actual TEXT_GENERATION_WEBUI_BASE_URL from environment."""
    return os.getenv("TEXT_GENERATION_WEBUI_BASE_URL", "http://localhost:5000/v1")


class TestProviderSpecificBaseUrls:
    """Test provider-specific base URL functionality."""

    def test_infers_provider_from_actual_text_generation_webui_base_url(self):
        """Test that provider is inferred from actual TEXT_GENERATION_WEBUI_BASE_URL."""
        # Use the actual environment variable or fall back to default
        tgwui_url = get_actual_tgwui_url()
        
        with patch.dict(os.environ, {"TEXT_GENERATION_WEBUI_BASE_URL": tgwui_url}):
            provider = resolve_provider()
            assert provider == "text-generation-webui"

    @patch.dict(os.environ, {
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
    })
    def test_infers_provider_from_fastchat_base_url(self, isolated_env):
        """Test that provider is inferred from FASTCHAT_BASE_URL."""
        provider = resolve_provider()
        assert provider == "fastchat"

    @patch.dict(os.environ, {
        "LMSTUDIO_BASE_URL": "http://localhost:1234/v1"
    })
    def test_infers_provider_from_lmstudio_base_url(self, isolated_env):
        """Test that provider is inferred from LMSTUDIO_BASE_URL."""
        provider = resolve_provider()
        assert provider == "lmstudio"

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": get_actual_tgwui_url(),
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
    })
    def test_prioritizes_first_provider_base_url_found(self):
        """Test that the first provider base URL found is used."""
        provider = resolve_provider()
        # Should be text-generation-webui (first in mapping)
        assert provider == "text-generation-webui"

    @patch.dict(os.environ, {
        "AI_PROVIDER": "openai"
    })
    def test_explicit_provider_overrides_env_base_url(self):
        """Test that explicit AI_PROVIDER takes precedence over env base URLs."""
        # Need to pass the env_provider parameter to resolve_provider
        provider = resolve_provider(env_provider=os.getenv("AI_PROVIDER"))
        assert provider == "openai"

    @patch.dict(os.environ, {
        "AI_BASE_URL": "http://custom-endpoint.com/v1"
    })
    def test_explicit_base_url_overrides_provider_specific(self):
        """Test that explicit base_url parameter takes precedence."""
        # Need to pass the settings_base_url parameter to resolve_base_url
        base_url = resolve_base_url("text-generation-webui", settings_base_url=os.getenv("AI_BASE_URL"))
        assert base_url == "http://custom-endpoint.com/v1"

    def test_no_provider_base_urls_returns_default(self):
        """Test that default provider is returned when no provider-specific URLs exist."""
        with patch.dict(os.environ, {}, clear=True):
            provider = resolve_provider()
            assert provider == "openai"


class TestBaseUrlResolution:
    """Test base URL resolution with provider-specific environment variables."""

    def test_resolves_actual_text_generation_webui_base_url(self):
        """Test that TEXT_GENERATION_WEBUI_BASE_URL is used for text-generation-webui provider."""
        # Use the actual environment variable or fall back to default
        tgwui_url = get_actual_tgwui_url()
        
        with patch.dict(os.environ, {"TEXT_GENERATION_WEBUI_BASE_URL": tgwui_url}):
            base_url = resolve_base_url("text-generation-webui")
            assert base_url == tgwui_url

    @patch.dict(os.environ, {
        "FASTCHAT_BASE_URL": "http://localhost:8000/v1"
    })
    def test_resolves_fastchat_base_url(self):
        """Test that FASTCHAT_BASE_URL is used for fastchat provider."""
        base_url = resolve_base_url("fastchat")
        assert base_url == "http://localhost:8000/v1"

    @patch.dict(os.environ, {
        "AI_BASE_URL": "http://custom-endpoint.com/v1"
    })
    def test_ai_base_url_takes_precedence(self):
        """Test that AI_BASE_URL takes precedence over provider-specific URLs."""
        # Need to pass the settings_base_url parameter to resolve_base_url
        base_url = resolve_base_url("text-generation-webui", settings_base_url=os.getenv("AI_BASE_URL"))
        assert base_url == "http://custom-endpoint.com/v1"

    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": get_actual_tgwui_url()
    })
    def test_per_request_base_url_takes_precedence(self):
        """Test that per-request base_url takes highest precedence."""
        base_url = resolve_base_url("text-generation-webui", base_url="http://override.com/v1")
        assert base_url == "http://override.com/v1"


class TestClientIntegration:
    """Test that AiClient works correctly with provider-specific base URLs."""

    def test_client_uses_actual_text_generation_webui_base_url(self):
        """Test that AiClient works correctly with actual TEXT_GENERATION_WEBUI_BASE_URL."""
        # Use the actual environment variable or fall back to default
        tgwui_url = get_actual_tgwui_url()
        tgwui_model = os.getenv("TEXT_GENERATION_WEBUI_MODEL", "local-model")
        
        # Remove AI_PROVIDER from environment to allow auto-detection
        original_ai_provider = os.environ.pop("AI_PROVIDER", None)
        
        try:
            with patch.dict(os.environ, {
                "TEXT_GENERATION_WEBUI_BASE_URL": tgwui_url,
                "TEXT_GENERATION_WEBUI_MODEL": tgwui_model
            }):
                # Create settings with provider=None to force auto-detection
                settings = AiSettings(provider=None, _env_file=None)
                client = AiClient(settings=settings)
                # Should use text-generation-webui provider and resolve its base URL
                assert client.settings.provider == "text-generation-webui"
                assert client.settings.base_url == tgwui_url
        finally:
            # Restore original AI_PROVIDER
            if original_ai_provider is not None:
                os.environ["AI_PROVIDER"] = original_ai_provider

    @patch.dict(os.environ, {
        "AI_PROVIDER": "openai",
        "TEXT_GENERATION_WEBUI_BASE_URL": get_actual_tgwui_url(),
        "OPENAI_API_KEY": "test-key"
    })
    def test_explicit_provider_overrides_base_url_inference(self):
        """Test that explicit AI_PROVIDER takes precedence over base URL inference."""
        # Create settings that will auto-detect from environment
        settings = AiSettings(_env_file=None)  # Force reload of env
        client = AiClient(settings=settings)
        # Should use openai (explicit provider) despite text-generation-webui base URL
        assert client.settings.provider == "openai"
        assert client.settings.base_url == "https://api.openai.com/v1"

    @patch.dict(os.environ, {
        "AI_BASE_URL": "http://custom.com/v1",
        "TEXT_GENERATION_WEBUI_BASE_URL": get_actual_tgwui_url(),
        "OPENAI_API_KEY": "test-key",
        "AI_MODEL": "gpt-3.5-turbo"
    })
    def test_explicit_base_url_overrides_provider_specific(self):
        """Test that explicit base_url parameter takes precedence."""
        # Create settings with explicit base_url
        settings = AiSettings(base_url="http://custom.com/v1", _env_file=None)
        client = AiClient(settings=settings)
        assert client.settings.base_url == "http://custom.com/v1"

    @pytest.mark.usefixtures("auto_patch_openai_boundary_functions")
    @patch.dict(os.environ, {
        "TEXT_GENERATION_WEBUI_BASE_URL": get_actual_tgwui_url(),
        "TEXT_GENERATION_WEBUI_MODEL": "local-model"
    })
    def test_provider_base_url_without_api_key_works(self):
        """Test that provider-specific base URL works without API key."""
        settings = AiSettings(provider="text-generation-webui", _env_file=None)  # Explicitly set provider
        client = AiClient(settings=settings)
        assert client.settings.provider == "text-generation-webui"
        assert client.settings.base_url == get_actual_tgwui_url()
        assert client.settings.api_key in (None, "webui")


class TestPrecedenceOrder:
    """Test the precedence order of base URL resolution."""

    def test_base_url_precedence_order(self):
        """Test that base URL resolution follows the correct precedence order."""
        # Test precedence: explicit base_url > provider-specific > default
        
        # 1. Explicit base_url should take precedence
        base_url = resolve_base_url("text-generation-webui", base_url="http://ai-base-url.com/v1")
        assert base_url == "http://ai-base-url.com/v1"

        # 2. Settings base_url should beat provider-specific
        base_url = resolve_base_url("text-generation-webui", settings_base_url="http://ai-base-url.com/v1")
        assert base_url == "http://ai-base-url.com/v1"

        # 3. Provider-specific should beat default
        with patch.dict(os.environ, {
            "TEXT_GENERATION_WEBUI_BASE_URL": get_actual_tgwui_url(),
        }):
            base_url = resolve_base_url("text-generation-webui")
            assert base_url == get_actual_tgwui_url()

        # 4. Default should be used when nothing else is available
        with patch.dict(os.environ, {}, clear=True):
            base_url = resolve_base_url("openai")
            assert base_url == "https://api.openai.com/v1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
