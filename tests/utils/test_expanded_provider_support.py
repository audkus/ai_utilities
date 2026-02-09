"""Tests for expanded provider support.

These tests verify that all providers documented in all-providers-guide.md
are properly supported in the config_resolver.
"""

import os
import pytest
from unittest.mock import patch

from ai_utilities.config_resolver import (
    resolve_provider,
    resolve_base_url,
    resolve_api_key,
    UnknownProviderError,
)


class TestExpandedProviderSupport:
    """Test that all documented providers are supported."""

    def test_all_documented_providers_are_valid(self):
        """Test that all providers from documentation are in valid_providers."""
        documented_providers = [
            "openai",
            "groq", 
            "together",
            "openrouter",
            "ollama",
            "lmstudio",
            "text-generation-webui",
            "fastchat",
            "openai_compatible",
            # Additional providers from documentation
            "anyscale",
            "fireworks",
            "replicate", 
            "vllm",
            "oobabooga",
            "localai",
            "azure",
            "google-vertex",
            "aws-bedrock",
            "ibm-watsonx",
        ]
        
        for provider in documented_providers:
            # Should not raise UnknownProviderError
            resolved = resolve_provider(provider=provider)
            assert resolved == provider.lower()

    def test_undocumented_provider_raises_error(self):
        """Test that unknown providers raise appropriate error."""
        with pytest.raises(UnknownProviderError):
            resolve_provider(provider="unknown-provider")

    def test_cloud_provider_base_urls(self):
        """Test base URLs for cloud providers."""
        cloud_providers = {
            "openai": "https://api.openai.com/v1",
            "groq": "https://api.groq.com/openai/v1", 
            "together": "https://api.together.xyz/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "anyscale": "https://api.endpoints.anyscale.com/v1",
            "fireworks": "https://api.fireworks.ai/inference/v1",
            "replicate": "https://api.replicate.com/v1",
        }
        
        for provider, expected_url in cloud_providers.items():
            base_url = resolve_base_url(provider)
            assert base_url == expected_url

    def test_local_provider_base_urls(self):
        """Test base URLs for local providers."""
        # Read from environment to match actual configuration
        import os
        
        local_providers = {
            "ollama": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            "lmstudio": os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            "text-generation-webui": os.getenv("TEXT_GENERATION_WEBUI_BASE_URL", "http://localhost:5000/v1"),
            "fastchat": os.getenv("FASTCHAT_BASE_URL", "http://localhost:8000/v1"),
            "vllm": os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
            "oobabooga": os.getenv("OOBABOOGA_BASE_URL", "http://localhost:7860/v1"),
            "localai": os.getenv("LOCALAI_BASE_URL", "http://localhost:8080/v1"),
        }
        
        for provider, expected_url in local_providers.items():
            base_url = resolve_base_url(provider)
            assert base_url == expected_url

    def test_enterprise_provider_base_urls(self):
        """Test base URLs for enterprise providers."""
        enterprise_providers = {
            "azure": "https://your-resource.openai.azure.com",
            "google-vertex": "https://us-central1-aiplatform.googleapis.com/v1",
            "aws-bedrock": "https://bedrock-runtime.us-east-1.amazonaws.com",
            "ibm-watsonx": "https://us-south.ml.cloud.ibm.com",
        }
        
        for provider, expected_url in enterprise_providers.items():
            base_url = resolve_base_url(provider)
            assert base_url == expected_url

    def test_provider_api_key_mappings(self):
        """Test API key environment variable mappings."""
        api_key_mappings = {
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY", 
            "openrouter": "OPENROUTER_API_KEY",
            "openai_compatible": "AI_API_KEY",
            "anyscale": "ANYSCALE_API_KEY",
            "fireworks": "FIREWORKS_API_KEY",
            "replicate": "REPLICATE_API_TOKEN",
            "azure": "AZURE_OPENAI_API_KEY",
            "google-vertex": "GOOGLE_APPLICATION_CREDENTIALS",
            "aws-bedrock": "AWS_ACCESS_KEY_ID",
            "ibm-watsonx": "IBM_CLOUD_API_KEY",
        }
        
        for provider, expected_env_var in api_key_mappings.items():
            env_vars = {expected_env_var: "test-key"}
            api_key = resolve_api_key(provider, env_vars=env_vars)
            assert api_key == "test-key"

    def test_openai_compatible_requires_base_url(self):
        """Test that openai_compatible provider requires base URL."""
        with pytest.raises(Exception):  # Should raise MissingBaseUrlError
            resolve_base_url("openai_compatible")

    def test_custom_base_url_overrides_default(self):
        """Test that custom base URL overrides provider default."""
        custom_url = "https://custom-endpoint.com/v1"
        
        for provider in ["openai", "groq", "anyscale", "ollama"]:
            base_url = resolve_base_url(provider, base_url=custom_url)
            assert base_url == custom_url

    def test_settings_base_url_overrides_default(self):
        """Test that settings base URL overrides provider default."""
        settings_url = "https://settings-endpoint.com/v1"
        
        for provider in ["openai", "groq", "anyscale", "ollama"]:
            base_url = resolve_base_url(provider, settings_base_url=settings_url)
            assert base_url == settings_url

    def test_provider_name_variations(self):
        """Test that provider name variations work correctly."""
        variations = {
            "OpenAI": "openai",
            "GROQ": "groq", 
            "Together": "together",
            "OpenRouter": "openrouter",
            "text-generation-webui": "text-generation-webui",
            "Google-Vertex": "google-vertex",
        }
        
        for input_name, expected_normalized in variations.items():
            resolved = resolve_provider(provider=input_name)
            assert resolved == expected_normalized


class TestDocumentationConsistency:
    """Test that documentation matches implementation."""

    def test_all_documented_providers_have_defaults(self):
        """Test that all documented providers have base URL defaults."""
        from ai_utilities.config_resolver import resolve_base_url
        
        documented_providers = [
            "openai", "groq", "together", "openrouter", "anyscale", "fireworks",
            "replicate", "ollama", "lmstudio", "text-generation-webui", "fastchat",
            "vllm", "oobabooga", "localai", "azure", "google-vertex", 
            "aws-bedrock", "ibm-watsonx"
        ]
        
        for provider in documented_providers:
            if provider != "openai_compatible":  # This one requires explicit base URL
                base_url = resolve_base_url(provider)
                assert base_url is not None
                assert base_url.startswith("http")

    def test_all_documented_providers_have_api_key_mappings(self):
        """Test that all documented providers have API key mappings."""
        from ai_utilities.config_resolver import resolve_api_key, MissingApiKeyError
        
        providers_requiring_keys = [
            "openai", "groq", "together", "openrouter", "anyscale", "fireworks",
            "replicate", "azure", "google-vertex", "aws-bedrock", "ibm-watsonx"
        ]
        
        for provider in providers_requiring_keys:
            # Should raise MissingApiKeyError when no env vars are set (not crash)
            with pytest.raises(MissingApiKeyError):
                resolve_api_key(provider, env_vars={})

    def test_local_providers_dont_require_api_keys(self):
        """Test that local providers work without API keys."""
        local_providers = ["ollama", "lmstudio", "text-generation-webui", "fastchat"]
        
        for provider in local_providers:
            base_url = resolve_base_url(provider)
            assert base_url is not None
            # Should work without API key environment variables
            api_key = resolve_api_key(provider, env_vars={})
            # Local providers get fallback keys, so should not raise exception
            assert api_key is not None


class TestRealWorldScenarios:
    """Test real-world usage scenarios for different providers."""

    @patch.dict(os.environ, {"ANYSCALE_API_KEY": "anyscale-test-key"})
    def test_anyscale_setup(self):
        """Test Anyscale provider setup as documented."""
        provider = resolve_provider(provider="anyscale")
        base_url = resolve_base_url(provider)
        api_key = resolve_api_key(provider, env_vars=dict(os.environ))
        
        assert provider == "anyscale"
        assert base_url == "https://api.endpoints.anyscale.com/v1"
        assert api_key == "anyscale-test-key"

    @patch.dict(os.environ, {"FIREWORKS_API_KEY": "fireworks-test-key"})
    def test_fireworks_setup(self):
        """Test Fireworks AI provider setup as documented."""
        provider = resolve_provider(provider="fireworks")
        base_url = resolve_base_url(provider)
        api_key = resolve_api_key(provider, env_vars=dict(os.environ))
        
        assert provider == "fireworks"
        assert base_url == "https://api.fireworks.ai/inference/v1"
        assert api_key == "fireworks-test-key"

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "azure-test-key"})
    def test_azure_setup(self):
        """Test Azure OpenAI provider setup as documented."""
        provider = resolve_provider(provider="azure")
        base_url = resolve_base_url(provider)
        api_key = resolve_api_key(provider, env_vars=dict(os.environ))
        
        assert provider == "azure"
        assert "azure" in base_url.lower()
        assert api_key == "azure-test-key"

    def test_ollama_local_setup(self):
        """Test Ollama local provider setup."""
        provider = resolve_provider(provider="ollama")
        base_url = resolve_base_url(provider)
        
        assert provider == "ollama"
        assert base_url == "http://localhost:11434/v1"
        assert "localhost" in base_url

    def test_openai_compatible_custom_endpoint(self):
        """Test openai_compatible with custom endpoint."""
        custom_url = "https://my-custom-endpoint.com/v1"
        
        provider = resolve_provider(provider="openai_compatible")
        base_url = resolve_base_url(provider, base_url=custom_url)
        
        assert provider == "openai_compatible"
        assert base_url == custom_url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
