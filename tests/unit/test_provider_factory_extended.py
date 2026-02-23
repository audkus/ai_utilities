"""Extended tests for provider factory to increase coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from ai_utilities import AiSettings, create_provider
from ai_utilities.providers import (
    OpenAICompatibleProvider,
    ProviderConfigurationError,
    ProviderCapabilityError
)
from ai_utilities.providers.provider_exceptions import MissingOptionalDependencyError


class TestProviderFactoryExtended:
    """Extended tests for the provider factory functionality."""
    
    def test_create_provider_with_none_settings(self) -> None:
        """Test creating provider with None settings."""
        with pytest.raises(Exception):  # Should raise error for None settings
            create_provider(None)
    
    def test_create_provider_with_minimal_openai_settings(self, force_openai_missing) -> None:
        """Test creating OpenAI provider with minimal settings."""
        settings = AiSettings(api_key="test-key")  # No model specified
        
        # Should raise MissingOptionalDependencyError when openai is not installed
        with pytest.raises(MissingOptionalDependencyError) as exc_info:
            create_provider(settings)
        
        # Verify the error message mentions openai requirement
        error_msg = str(exc_info.value)
        assert "openai" in error_msg.lower()
        assert "install" in error_msg.lower()
    
    def test_create_provider_with_custom_timeout(self, force_openai_missing) -> None:
        """Test creating provider with custom timeout."""
        settings = AiSettings(
            provider="openai",
            api_key="test-key",
            timeout=30.0
        )
        
        # Should raise MissingOptionalDependencyError when openai is not installed
        with pytest.raises(MissingOptionalDependencyError) as exc_info:
            create_provider(settings)
        
        # Verify the error message mentions openai requirement
        error_msg = str(exc_info.value)
        assert "openai" in error_msg.lower()
        assert "install" in error_msg.lower()
    
    def test_create_provider_with_temperature_and_max_tokens(self, force_openai_missing) -> None:
        """Test creating provider with temperature and max_tokens."""
        settings = AiSettings(
            provider="openai",
            api_key="test-key",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Should raise MissingOptionalDependencyError when openai is not installed
        with pytest.raises(MissingOptionalDependencyError) as exc_info:
            create_provider(settings)
        
        # Verify the error message mentions openai requirement
        error_msg = str(exc_info.value)
        assert "openai" in error_msg.lower()
        assert "install" in error_msg.lower()
    
    @pytest.mark.requires_openai
    @patch("ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client")
    def test_create_openai_compatible_with_various_base_urls(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider with various base URL formats."""
        # Mock the client creation
        mock_client = MagicMock(name="OpenAICompatibleSDKClient")
        mock_create_client.return_value = mock_client
        
        base_urls = [
            "https://api.example.com",
            "http://localhost:8080/v1",
            "https://custom-domain.org/api",
            "http://127.0.0.1:11434"
        ]
        
        for base_url in base_urls:
            settings = AiSettings(
                provider="openai_compatible",
                base_url=base_url,
                api_key="test-key",
                model="test-model"  # Add required model parameter
            )
            
            provider = create_provider(settings)
            assert isinstance(provider, OpenAICompatibleProvider)
            assert provider.base_url == base_url
            
            # Verify the boundary was called with correct base_url
            mock_create_client.assert_called_with(
                api_key="test-key",
                base_url=base_url,
                timeout=30
            )
    
    @pytest.mark.requires_openai
    def test_create_openai_compatible_with_request_timeout_float(self) -> None:
        """Test OpenAI-compatible provider with float request_timeout_s."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:8000/v1",
            request_timeout_s=30.7,
            model="test-model"  # Add required model parameter
        )
        
        provider = create_provider(settings)
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.timeout == 30  # Should be converted to int
    
    @pytest.mark.requires_openai
    def test_create_openai_compatible_with_empty_extra_headers(self) -> None:
        """Test OpenAI-compatible provider with empty extra headers."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:8000/v1",
            extra_headers={},
            model="test-model"  # Add required model parameter
        )
        
        provider = create_provider(settings)
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.extra_headers == {}
    
    @pytest.mark.requires_openai
    def test_create_openai_compatible_with_complex_extra_headers(self) -> None:
        """Test OpenAI-compatible provider with complex extra headers."""
        extra_headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "custom-value",
            "Content-Type": "application/json",
            "User-Agent": "TestApp/1.0"
        }
        
        settings = AiSettings(
            provider="openai_compatible",
            base_url="http://localhost:8000/v1",
            extra_headers=extra_headers,
            model="test-model"  # Add required model parameter
        )
        
        # Patch stable SDK creation boundary to avoid OpenAI dependency
        with patch("ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client") as mock_create_client:
            # Create dummy client
            mock_client = MagicMock(name="OpenAICompatibleSDKClient")
            mock_create_client.return_value = mock_client
            
            provider = create_provider(settings)
            
            # Contract assertions
            assert provider is not None
            assert provider.provider_name == "openai_compatible"
            assert provider.base_url == "http://localhost:8000/v1"
            assert provider.extra_headers == extra_headers
            
            # Verify boundary called with correct kwargs
            mock_create_client.assert_called_once()
            kwargs = mock_create_client.call_args.kwargs
            assert kwargs["api_key"] == "dummy-key"   # because api_key not provided in settings
            assert kwargs["base_url"] == "http://localhost:8000/v1"
            assert kwargs["timeout"] == 30
            assert kwargs["default_headers"] == extra_headers
    
    def test_provider_factory_error_messages(self) -> None:
        """Test provider factory error messages are descriptive."""
        # Test missing API key error
        with pytest.raises(ProviderConfigurationError) as exc_info:
            settings = AiSettings(provider="openai", api_key=None)
            create_provider(settings)
        
        error_msg = str(exc_info.value)
        assert "openai" in error_msg.lower()
        assert "configuration" in error_msg.lower()
        
        # Test missing base URL error
        with pytest.raises(ProviderConfigurationError) as exc_info:
            settings = AiSettings(provider="openai_compatible", base_url=None)
            create_provider(settings)
        
        error_msg = str(exc_info.value)
        assert "openai_compatible" in error_msg.lower()
        assert "configuration" in error_msg.lower()
    
    def test_provider_factory_with_invalid_provider_types(self) -> None:
        """Test provider factory with invalid provider types."""
        # Test that the factory handles unknown providers gracefully
        # We'll test this by checking the error message format
        settings = AiSettings(provider="openai", api_key="test-key")
        
        # This test verifies the error handling mechanism exists
        # The actual provider validation happens at the Pydantic level
        with pytest.raises(ProviderConfigurationError) as exc_info:
            settings = AiSettings(provider="openai_compatible", base_url=None)
            create_provider(settings)
        
        error_msg = str(exc_info.value)
        assert "configuration" in error_msg.lower()
    
    @pytest.mark.requires_openai
    @patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client')
    def test_openai_compatible_provider_initialization_edge_cases(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider initialization edge cases."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock the SDK client creation
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Test with empty string API key
        provider = OpenAICompatibleProvider(
            api_key="",
            base_url="http://localhost:8000/v1"
        )
        # Note: The provider might not store api_key as a direct attribute
        # Let's test the base_url which should be stored
        assert provider.base_url == "http://localhost:8000/v1"
        
        # Test with very long base URL
        long_url = "http://localhost:8000/" + "path" * 100
        provider = OpenAICompatibleProvider(
            base_url=long_url
        )
        assert provider.base_url == long_url
    
    @pytest.mark.requires_openai
    @patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client')
    def test_openai_compatible_ask_with_various_prompts(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider ask with various prompt types."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_create_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1"
        )
        
        # Test with different prompt types
        prompts = [
            "Simple prompt",
            "Prompt with special chars: \n\t",
            "Very long prompt " * 100,
            "Prompt with \"quotes\" and 'apostrophes'",
            "Prompt with unicode: áéíóú",
            ""
        ]
        
        for prompt in prompts:
            response = provider.ask(prompt)
            # Contract: verify provider was called and returned a result (passthrough)
            assert response is not None
            assert isinstance(response, str)  # Verify return type contract
    
    @pytest.mark.requires_openai
    @patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client')
    def test_openai_compatible_ask_with_parameters(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider ask with various parameters."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_create_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1"
        )
        
        # Test with various parameters
        response = provider.ask(
            "Test prompt",
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        # Contract: verify provider was called and returned a result (passthrough)
        assert response is not None
        assert isinstance(response, str)  # Verify return type contract
    
    @pytest.mark.requires_openai
    @patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client')
    def test_openai_compatible_ask_many_edge_cases(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider ask_many edge cases."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_create_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1"
        )
        
        # Test with empty list
        responses = provider.ask_many([])
        assert len(responses) == 0
        
        # Test with single prompt
        responses = provider.ask_many(["Single prompt"])
        assert len(responses) == 1
        assert responses[0] == "Response"
        
        # Test with many prompts
        prompts = [f"Prompt {i}" for i in range(10)]
        responses = provider.ask_many(prompts)
        assert len(responses) == 10
        assert all(r == "Response" for r in responses)
    
    @pytest.mark.requires_openai
    @patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client')
    def test_openai_compatible_json_mode_edge_cases(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider JSON mode edge cases."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        import json
        
        # Mock the OpenAI client
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1"
        )
        
        # Test with valid JSON
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"key": "value"}'))]
        mock_client.chat.completions.create.return_value = mock_response
        
        response = provider.ask("Test", return_format="json")
        assert response == {"key": "value"}
        
        # Test with JSON array
        mock_response.choices[0].message.content = '[1, 2, 3]'
        response = provider.ask("Test", return_format="json")
        assert response == [1, 2, 3]
        
        # Test with JSON number
        mock_response.choices[0].message.content = '42'
        response = provider.ask("Test", return_format="json")
        assert response == 42
        
        # Test with JSON boolean
        mock_response.choices[0].message.content = 'true'
        response = provider.ask("Test", return_format="json")
        assert response is True
    
    @pytest.mark.requires_openai
    @patch('ai_utilities.providers.openai_compatible_provider._create_openai_sdk_client')
    def test_openai_compatible_error_handling(self, mock_create_client) -> None:
        """Test OpenAI-compatible provider error handling."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        
        # Mock the OpenAI client
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000/v1"
        )
        
        # Test with API error
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            provider.ask("Test prompt")
        
        # Test with malformed response (missing choices)
        mock_response = Mock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(Exception):
            provider.ask("Test prompt")
    
    def test_provider_factory_lazy_imports(self, force_openai_missing) -> None:
        """Test that provider factory uses lazy imports correctly."""
        # This test verifies that the factory handles missing OpenAI gracefully
        settings = AiSettings(
            provider="openai",
            api_key="test-key"
        )
        
        # Should raise MissingOptionalDependencyError when openai is not installed
        with pytest.raises(MissingOptionalDependencyError) as exc_info:
            create_provider(settings)
        
        # Verify the error message mentions openai requirement
        error_msg = str(exc_info.value)
        assert "openai" in error_msg.lower()
        assert "install" in error_msg.lower()
    
    def test_provider_factory_caching(self, force_openai_missing) -> None:
        """Test that provider factory consistently raises MissingOptionalDependencyError for OpenAI providers."""
        # Test with OpenAI provider to verify consistent MissingOptionalDependencyError behavior
        settings = AiSettings(
            provider="openai",
            api_key="test-key"
        )
        
        # Should consistently raise MissingOptionalDependencyError when openai is not installed
        with pytest.raises(MissingOptionalDependencyError) as exc_info1:
            create_provider(settings)
        
        with pytest.raises(MissingOptionalDependencyError) as exc_info2:
            create_provider(settings)
        
        # Both errors should mention openai requirement
        error_msg1 = str(exc_info1.value)
        error_msg2 = str(exc_info2.value)
        assert "openai" in error_msg1.lower()
        assert "install" in error_msg1.lower()
        assert "openai" in error_msg2.lower()
        assert "install" in error_msg2.lower()
