"""Tests for provider factory and OpenAI-compatible provider."""

import pytest
from unittest.mock import Mock, patch

from ai_utilities import AiSettings, create_provider
from ai_utilities.providers import (
    OpenAIProvider, 
    OpenAICompatibleProvider,
    ProviderConfigurationError,
    ProviderCapabilityError
)


class TestProviderFactory:
    """Test the provider factory functionality."""
    
    def test_create_openai_provider_default(self):
        """Test creating OpenAI provider with default settings."""
        settings = AiSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        
        provider = create_provider(settings)
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.settings.api_key == "test-key"
        assert provider.settings.model == "gpt-4"
    
    def test_create_openai_provider_explicit(self):
        """Test creating OpenAI provider with explicit provider override."""
        settings = AiSettings(provider="openai", api_key="test-key")
        mock_provider = Mock()
        
        provider = create_provider(settings, mock_provider)
        
        assert provider is mock_provider
    
    def test_create_openai_compatible_provider(self):
        """Test creating OpenAI-compatible provider."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:11434/v1",
            api_key="dummy-key",
            timeout=60
        )
        
        provider = create_provider(settings)
        
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.base_url == "http://localhost:11434/v1"
        assert provider.timeout == 60
    
    def test_openai_compatible_with_request_timeout_s(self):
        """Test OpenAI-compatible provider with request_timeout_s."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:8000/v1",
            request_timeout_s=45.5,
            timeout=30  # Should be overridden
        )
        
        provider = create_provider(settings)
        
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.timeout == 45  # Converted to int
    
    def test_openai_compatible_with_extra_headers(self):
        """Test OpenAI-compatible provider with extra headers."""
        extra_headers = {"Authorization": "Bearer custom-token", "X-Custom": "value"}
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:8000/v1",
            extra_headers=extra_headers
        )
        
        provider = create_provider(settings)
        
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.extra_headers == extra_headers
    
    def test_openai_provider_missing_api_key(self, monkeypatch):
        """Test OpenAI provider fails without API key."""
        # Clear environment variables to ensure test isolation
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        
        settings = AiSettings(provider="openai", api_key=None)
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings)
        
        assert "API key is required" in str(exc_info.value)
        assert "openai" in str(exc_info.value)
    
    def test_openai_compatible_missing_base_url(self):
        """Test OpenAI-compatible provider fails without base_url."""
        settings = AiSettings(provider="openai_compatible", base_url=None)
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings)
        
        assert "base_url is required" in str(exc_info.value)
        assert "openai_compatible" in str(exc_info.value)
    
    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        # Create settings with valid provider first, then change it
        settings = AiSettings(provider="openai")
        settings.provider = "unknown"  # Direct assignment to bypass validation
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings)
        
        assert "Unknown provider: unknown" in str(exc_info.value)


class TestOpenAICompatibleProvider:
    """Test the OpenAI-compatible provider functionality."""
    
    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_initialization_with_base_url(self, mock_openai):
        """Test provider initialization requires base_url."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Should raise error without base_url
        with pytest.raises(ProviderConfigurationError):
            OpenAICompatibleProvider(api_key="test")
        
        # Should work with base_url
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:11434/v1"
        )
        
        assert provider.base_url == "http://localhost:11434/v1"
        mock_openai.assert_called_once()
    
    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_initialization_with_extra_headers(self, mock_openai):
        """Test provider initialization with extra headers."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        extra_headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1",
            extra_headers=extra_headers
        )
        
        call_args = mock_openai.call_args[1]
        assert call_args["default_headers"] == extra_headers
    
    @patch('ai_utilities.providers.openai_compatible_provider.logger')
    def test_capability_checking(self, mock_logger):
        """Test provider capability checking."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:11434/v1"
        )
        
        # Should not raise for supported capabilities
        provider._check_capability("text")  # Not in capability map, should pass
        provider._check_capability("json_mode")  # Now supported
        
        # Should raise for unsupported capabilities
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider._check_capability("streaming")
        
        assert "streaming" in str(exc_info.value)
        assert "openai_compatible" in str(exc_info.value)
    
    @patch('ai_utilities.providers.openai_compatible_provider.logger')
    def test_prepare_request_params_filters_unsupported(self, mock_logger):
        """Test request parameter preparation filters unsupported params."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:11434/v1"
        )
        
        params = provider._prepare_request_params(
            temperature=0.5,
            max_tokens=100,
            top_p=0.9,  # Unsupported
            frequency_penalty=0.1,  # Unsupported
            model="llama2"
        )
        
        # Should include supported parameters
        assert params["temperature"] == 0.5
        assert params["max_tokens"] == 100
        assert params["model"] == "llama2"
        
        # Should not include unsupported parameters
        assert "top_p" not in params
        assert "frequency_penalty" not in params
        
        # Should log warnings for unsupported parameters
        assert mock_logger.warning.call_count == 2
    
    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_text_mode(self, mock_openai):
        """Test ask method in text mode."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:11434/v1"
        )
        
        response = provider.ask("Test prompt", return_format="text")
        
        assert response == "Test response"
        mock_openai.return_value.chat.completions.create.assert_called_once()
    
    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_json_mode_with_warning(self, mock_openai):
        """Test ask method in JSON mode with capability warning."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:11434/v1"
        )
        
        with patch('ai_utilities.providers.openai_compatible_provider.logger') as mock_logger:
            response = provider.ask("Test prompt", return_format="json")
            
            # Should warn about JSON mode not being guaranteed
            mock_logger.warning.assert_called_with(
                "JSON mode requested but not guaranteed to be supported by this OpenAI-compatible provider"
            )
        
        assert response == {"key": "value"}
    
    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_json_mode_parse_error(self, mock_openai):
        """Test ask method handles JSON parse errors gracefully."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON {"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:11434/v1"
        )
        
        with patch('ai_utilities.providers.openai_compatible_provider.logger') as mock_logger:
            response = provider.ask("Test prompt", return_format="json")
            
            # Should log error but return raw text
            mock_logger.error.assert_called()
        
        assert response == "Invalid JSON {"
    
    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_many(self, mock_openai):
        """Test ask_many method."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:11434/v1"
        )
        
        responses = provider.ask_many(["Prompt 1", "Prompt 2"])
        
        assert len(responses) == 2
        assert all(r == "Response" for r in responses)
        assert mock_openai.return_value.chat.completions.create.call_count == 2
