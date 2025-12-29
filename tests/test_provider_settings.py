"""Tests for provider-related settings functionality."""

import json
import pytest
from unittest.mock import patch

from ai_utilities import AiSettings


class TestProviderSettings:
    """Test provider-related settings functionality."""
    
    def test_default_provider_is_openai(self):
        """Test default provider is OpenAI."""
        settings = AiSettings()
        assert settings.provider == "openai"
    
    def test_explicit_provider_setting(self):
        """Test explicit provider setting."""
        settings = AiSettings(provider="openai_compatible")
        assert settings.provider == "openai_compatible"
    
    def test_provider_environment_variable(self):
        """Test provider can be set via environment variable."""
        with patch.dict('os.environ', {'AI_PROVIDER': 'openai_compatible'}):
            settings = AiSettings()
            assert settings.provider == "openai_compatible"
    
    def test_base_url_environment_variable(self):
        """Test base_url can be set via environment variable."""
        with patch.dict('os.environ', {'AI_BASE_URL': 'http://localhost:11434/v1'}):
            settings = AiSettings()
            assert settings.base_url == "http://localhost:11434/v1"
    
    def test_request_timeout_s_environment_variable(self):
        """Test request_timeout_s can be set via environment variable."""
        with patch.dict('os.environ', {'AI_REQUEST_TIMEOUT_S': '45.5'}):
            settings = AiSettings()
            assert settings.request_timeout_s == 45.5
    
    def test_extra_headers_environment_variable(self):
        """Test extra_headers can be set via environment variable as JSON."""
        headers_json = '{"Authorization": "Bearer token", "X-Custom": "value"}'
        with patch.dict('os.environ', {'AI_EXTRA_HEADERS': headers_json}):
            settings = AiSettings()
            assert settings.extra_headers == {"Authorization": "Bearer token", "X-Custom": "value"}
    
    def test_extra_headers_invalid_json(self):
        """Test invalid JSON for extra_headers raises error."""
        with patch.dict('os.environ', {'AI_EXTRA_HEADERS': 'invalid-json'}):
            with pytest.raises(ValueError) as exc_info:
                AiSettings()
            
            # Pydantic v2 gives a specific error message format
            error_message = str(exc_info.value)
            assert "dict_type" in error_message or "Invalid JSON" in error_message
    
    def test_openai_compatible_settings_validation(self):
        """Test OpenAI-compatible provider settings."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:8000/v1",
            api_key="dummy-key",
            request_timeout_s=60.0,
            extra_headers={"X-Custom": "value"}
        )
        
        assert settings.provider == "openai_compatible"
        assert settings.base_url == "http://localhost:8000/v1"
        assert settings.api_key == "dummy-key"
        assert settings.request_timeout_s == 60.0
        assert settings.extra_headers == {"X-Custom": "value"}
    
    def test_openai_settings_validation(self):
        """Test OpenAI provider settings."""
        settings = AiSettings(
            provider="openai",
            api_key="sk-test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert settings.provider == "openai"
        assert settings.api_key == "sk-test-key"
        assert settings.model == "gpt-4"
        assert settings.temperature == 0.5
        assert settings.max_tokens == 1000
    
    def test_provider_field_validation(self):
        """Test provider field accepts valid values and factory handles invalid ones."""
        # Should accept valid values
        settings1 = AiSettings(provider="openai")
        assert settings1.provider == "openai"
        
        settings2 = AiSettings(provider="openai_compatible")
        assert settings2.provider == "openai_compatible"
        
        # Factory should handle invalid values (not Pydantic validation)
        from ai_utilities.providers.provider_factory import create_provider, ProviderConfigurationError
        
        settings_invalid = AiSettings()
        settings_invalid.provider = "invalid_provider"  # Direct assignment to bypass validation
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings_invalid)
        
        assert "Unknown provider: invalid_provider" in str(exc_info.value)
    
    def test_timeout_and_request_timeout_s_interaction(self):
        """Test interaction between timeout and request_timeout_s."""
        # When request_timeout_s is set, it should be preferred
        settings = AiSettings(timeout=30, request_timeout_s=60.0)
        assert settings.timeout == 30
        assert settings.request_timeout_s == 60.0
        
        # When only timeout is set, request_timeout_s should be None
        settings = AiSettings(timeout=30)
        assert settings.timeout == 30
        assert settings.request_timeout_s is None
    
    def test_extra_headers_optional(self):
        """Test extra_headers is optional."""
        settings = AiSettings()
        assert settings.extra_headers is None
        
        settings = AiSettings(extra_headers={})
        assert settings.extra_headers == {}
    
    def test_api_key_optional_for_compatible_provider(self):
        """Test API key is optional for openai_compatible provider."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:11434/v1"
            # api_key not provided
        )
        assert settings.api_key is None
    
    def test_settings_with_all_fields(self):
        """Test settings with all provider-related fields."""
        extra_headers = {"Authorization": "Bearer token", "X-Model": "llama2"}
        settings = AiSettings(
            provider="openai_compatible",
            api_key="test-key",
            model="llama2-7b",
            temperature=0.8,
            max_tokens=2048,
            base_url="http://localhost:11434/v1",
            timeout=30,
            request_timeout_s=45.0,
            extra_headers=extra_headers,
            usage_scope="per_process",
            usage_client_id="test-client"
        )
        
        # Verify all fields are set correctly
        assert settings.provider == "openai_compatible"
        assert settings.api_key == "test-key"
        assert settings.model == "llama2-7b"
        assert settings.temperature == 0.8
        assert settings.max_tokens == 2048
        assert settings.base_url == "http://localhost:11434/v1"
        assert settings.timeout == 30
        assert settings.request_timeout_s == 45.0
        assert settings.extra_headers == extra_headers
        assert settings.usage_scope == "per_process"
        assert settings.usage_client_id == "test-client"
