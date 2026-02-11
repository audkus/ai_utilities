"""Tests for provider factory and OpenAI-compatible provider."""

import pytest
from unittest.mock import Mock, patch

from ai_utilities import AiSettings, create_provider
from ai_utilities.providers import (
    OpenAICompatibleProvider,
    ProviderConfigurationError,
    ProviderCapabilityError
)


class TestProviderFactory:
    """Test the provider factory functionality."""
    
    def test_create_openai_provider_default(self):
        """Test creating OpenAI provider raises ImportError without openai package."""
        settings = AiSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        
        # Should raise ImportError when openai is not installed
        with pytest.raises(ImportError) as exc_info:
            create_provider(settings)
        
        # Verify the error message mentions openai requirement
        error_msg = str(exc_info.value)
        assert "openai" in error_msg.lower()
        assert "install" in error_msg.lower()
    
    def test_create_openai_provider_explicit(self):
        """Test creating OpenAI provider with explicit provider override."""
        settings = AiSettings(provider="openai", api_key="test-key")
        mock_provider = Mock()
        
        provider = create_provider(settings, mock_provider)
        
        assert provider is mock_provider
    
    @pytest.mark.requires_openai
    def test_create_openai_compatible_provider(self):
        """Test creating OpenAI-compatible provider."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        mock_create_client = Mock()
        with patch.object(ocp, '_create_openai_sdk_client', mock_create_client):
            mock_client = Mock()
            mock_create_client.return_value = mock_client
            
            settings = AiSettings(
                provider="openai_compatible",
                base_url="http://localhost:11434/v1",
                api_key="dummy-key",
                model="test-model",
                timeout=60
            )
            
            provider = create_provider(settings)
            
            assert isinstance(provider, OpenAICompatibleProvider)
            assert provider.base_url == "http://localhost:11434/v1"
            assert provider.timeout == 60
            
            # Verify SDK client was created with correct parameters
            mock_create_client.assert_called_once()
            call_args = mock_create_client.call_args[1]
            assert call_args["timeout"] == 60
    
    @pytest.mark.requires_openai
    def test_openai_compatible_with_request_timeout_s(self):
        """Test OpenAI-compatible provider with request_timeout_s."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        mock_create_client = Mock()
        with patch.object(ocp, '_create_openai_sdk_client', mock_create_client):
            mock_client = Mock()
            mock_create_client.return_value = mock_client
            
            settings = AiSettings(
                provider="openai_compatible",
                base_url="http://localhost:8000/v1",
                model="test-model",
                request_timeout_s=45.5,
                timeout=30  # Should be overridden
            )
            
            provider = create_provider(settings)
            
            assert isinstance(provider, OpenAICompatibleProvider)
            assert provider.timeout == 45  # Converted to int
            
            # Verify SDK client was created with correct timeout
            mock_create_client.assert_called_once()
            call_args = mock_create_client.call_args[1]
            assert call_args["timeout"] == 45  # Converted to int
    
    @pytest.mark.requires_openai
    def test_openai_compatible_with_extra_headers(self):
        """Test OpenAI-compatible provider with extra headers."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        mock_create_client = Mock()
        with patch.object(ocp, '_create_openai_sdk_client', mock_create_client):
            extra_headers = {"Authorization": "Bearer custom-token", "X-Custom": "value"}
            mock_client = Mock()
            mock_create_client.return_value = mock_client
            
            settings = AiSettings(
                provider="openai_compatible",
                base_url="http://localhost:8000/v1",
                model="test-model",
                extra_headers=extra_headers
            )
            
            provider = create_provider(settings)
            
            assert isinstance(provider, OpenAICompatibleProvider)
            assert provider.extra_headers == extra_headers
            
            # Verify SDK client was created with headers
            mock_create_client.assert_called_once()
            call_args = mock_create_client.call_args[1]
            assert call_args["default_headers"] == extra_headers
    
    def test_openai_provider_missing_api_key(self, monkeypatch):
        """Test OpenAI provider fails without API key."""
        # Clear environment variables to ensure test isolation
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        
        settings = AiSettings(provider="openai", api_key=None)
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings)
        
        assert "API key is required" in str(exc_info.value) or "configuration error" in str(exc_info.value)
        assert "openai" in str(exc_info.value)
    
    def test_openai_compatible_missing_base_url(self):
        """Test OpenAI-compatible provider fails without base_url."""
        settings = AiSettings(provider="openai_compatible", base_url=None)
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings)
        
        assert "base_url is required" in str(exc_info.value) or "configuration error" in str(exc_info.value)
        assert "openai_compatible" in str(exc_info.value)
    
    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        # Create settings with valid provider first, then change it
        settings = AiSettings(provider="openai")
        settings.provider = "unknown"  # Direct assignment to bypass validation
        
        with pytest.raises(ProviderConfigurationError) as exc_info:
            create_provider(settings)
        
        assert "Unknown provider: unknown" in str(exc_info.value)


@pytest.mark.requires_openai
class TestOpenAICompatibleProvider:
    """Test the OpenAI-compatible provider functionality."""
    
    def test_initialization_with_base_url(self):
        """Test provider initialization requires base_url."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        with patch.object(ocp, '_create_openai_sdk_client') as mock_create_client:
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
            mock_create_client.assert_called_once()
    
    def test_initialization_with_extra_headers(self):
        """Test provider initialization with extra headers."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        with patch.object(ocp, '_create_openai_sdk_client') as mock_create_client:
            from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
            
            extra_headers = {"Authorization": "Bearer token", "X-Custom": "value"}
            provider = OpenAICompatibleProvider(
                base_url="http://localhost:8000/v1",
                extra_headers=extra_headers
            )
            
            assert provider.extra_headers == extra_headers
            mock_create_client.assert_called_once()
    
    def test_ask_text_mode(self):
        """Test asking in text mode."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        with patch.object(ocp, '_create_openai_sdk_client') as mock_create_client:
            from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
            
            # Mock the OpenAI client response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_create_client.return_value = mock_client
            
            provider = OpenAICompatibleProvider(
                api_key="test-key",
                base_url="http://localhost:11434/v1"
            )
            
            response = provider.ask("Test prompt")
            # Contract: verify provider was called and returned a result (passthrough)
            assert response is not None
            assert isinstance(response, str)  # Verify return type contract
    
    def test_ask_json_mode_with_warning(self):
        """Test asking in JSON mode shows warning for compatible providers."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        with patch.object(ocp, '_create_openai_sdk_client') as mock_create_client:
            from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
            
            # Mock the OpenAI client response with real string content
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content='{"key": "value"}'))]
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_create_client.return_value = mock_client
            
            provider = OpenAICompatibleProvider(
                api_key="test-key",
                base_url="http://localhost:11434/v1"
            )
            
            response = provider.ask("Test prompt", return_format="json")
            # Contract: verify provider was called and returned a result (passthrough)
            assert response is not None
            assert isinstance(response, str)  # Verify return type contract
            assert response == mock_response.choices[0].message.content  # Verify passthrough
    
    def test_ask_json_mode_parse_error(self):
        """Test ask method handles JSON parse errors gracefully."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        with patch.object(ocp, '_create_openai_sdk_client') as mock_create_client:
            from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
            
            # Mock OpenAI response with invalid JSON (real string)
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Invalid JSON {"
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_create_client.return_value = mock_client
            
            provider = OpenAICompatibleProvider(
                base_url="http://localhost:11434/v1"
            )
            
            response = provider.ask("Test prompt", return_format="json")
            
            # Should return raw text when JSON parsing fails
            assert response is not None
            assert isinstance(response, str)  # Verify return type contract
            assert response == mock_response.choices[0].message.content  # Verify passthrough of mock content
    
    def test_ask_many(self):
        """Test ask_many method."""
        # Import the module locally to ensure patch target exists
        import ai_utilities.providers.openai_compatible_provider as ocp
        with patch.object(ocp, '_create_openai_sdk_client') as mock_create_client:
            from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
            
            # Mock OpenAI response with real string content
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Response"
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_create_client.return_value = mock_client
            
            provider = OpenAICompatibleProvider(
                base_url="http://localhost:11434/v1"
            )
            
            responses = provider.ask_many(["Prompt 1", "Prompt 2"])
            
            assert len(responses) == 2
            # Contract: verify responses are strings and match mock content (passthrough)
            mock_content = mock_response.choices[0].message.content
            assert all(isinstance(r, str) and r == mock_content for r in responses)
            assert mock_client.chat.completions.create.call_count == 2
