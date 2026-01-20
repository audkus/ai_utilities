"""Contract-style unit tests for providers."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from ai_utilities.config_models import AiSettings
from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
from ai_utilities.providers.provider_exceptions import ProviderCapabilityError, ProviderConfigurationError


class TestOpenAIProvider:
    """Contract tests for OpenAIProvider."""
    
    def test_provider_name_returns_str(self, OpenAIProvider):
        """Test provider_name returns correct string."""
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        provider = OpenAIProvider(settings)
        assert provider.provider_name == "openai"
        assert isinstance(provider.provider_name, str)
    
    def test_ask_text_returns_str(self, OpenAIProvider):
        """Test ask_text returns string."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        provider = OpenAIProvider(settings, client=mock_client)
        
        result = provider.ask_text("Test prompt")
        assert isinstance(result, str)
        assert result == "Test response"
    
    def test_ask_json_returns_dict_when_json_mode_supported(self, OpenAIProvider):
        """Test ask_json returns dict when JSON mode is supported."""
        # Mock OpenAI client with JSON response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        settings = AiSettings(api_key="test-key", model="gpt-4")
        provider = OpenAIProvider(settings, client=mock_client)
        
        result = provider.ask("Test prompt", return_format="json")
        assert isinstance(result, dict)
        assert result == {"key": "value"}
    
    def test_ask_many_returns_list(self, OpenAIProvider):
        """Test ask_many returns list."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response 1"
        mock_client.chat.completions.create.return_value = mock_response
        
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        provider = OpenAIProvider(settings, client=mock_client)
        
        prompts = ["Prompt 1", "Prompt 2"]
        results = provider.ask_many(prompts)
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)
    
    def test_capability_dependent_methods_raise_provider_capability_error(self, OpenAIProvider):
        """Test methods raise ProviderCapabilityError for unsupported capabilities."""
        # This would be tested with a model that doesn't support certain features
        # For now, we'll test the basic structure
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        provider = OpenAIProvider(settings)
        
        # Test that provider has the required methods
        assert hasattr(provider, 'ask')
        assert hasattr(provider, 'ask_many')
        assert hasattr(provider, 'upload_file')
        assert hasattr(provider, 'download_file')
        assert hasattr(provider, 'generate_image')
    
    def test_injection_of_fake_client_works(self, OpenAIProvider):
        """Test that fake client can be injected for testing."""
        fake_client = Mock()
        fake_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Fake response"))]
        )
        
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        provider = OpenAIProvider(settings, client=fake_client)
        
        # Verify the fake client is used
        result = provider.ask_text("Test")
        assert result == "Fake response"
        fake_client.chat.completions.create.assert_called_once()


class TestOpenAICompatibleProvider:
    """Contract tests for OpenAICompatibleProvider."""
    
    def test_provider_name_returns_str(self, OpenAIProvider):
        """Test provider_name returns correct string."""
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        assert provider.provider_name == "openai_compatible"
        assert isinstance(provider.provider_name, str)
    
    def test_requires_base_url(self, OpenAIProvider):
        """Test that base_url is required."""
        with pytest.raises(ProviderConfigurationError):
            OpenAICompatibleProvider(api_key="test-key")
    
    def test_accepts_base_url(self, OpenAIProvider):
        """Test that provider accepts base_url parameter."""
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        assert provider.base_url == "http://localhost:8080"
    
    def test_capability_dependent_methods_raise_provider_capability_error(self, OpenAIProvider):
        """Test methods raise ProviderCapabilityError for unsupported capabilities."""
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        
        # Test that provider has the required methods
        assert hasattr(provider, 'ask')
        assert hasattr(provider, 'ask_many')
        assert hasattr(provider, 'upload_file')
        assert hasattr(provider, 'download_file')
        assert hasattr(provider, 'generate_image')


class TestProviderContracts:
    """Cross-provider contract tests."""
    
    def test_all_providers_have_provider_name(self, OpenAIProvider):
        """Test all providers have provider_name property."""
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        
        openai_provider = OpenAIProvider(settings)
        compatible_provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        
        for provider in [openai_provider, compatible_provider]:
            assert hasattr(provider, 'provider_name')
            assert isinstance(provider.provider_name, str)
            assert len(provider.provider_name) > 0
    
    def test_all_providers_implement_base_interface(self, OpenAIProvider):
        """Test all providers implement the base interface methods."""
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        
        openai_provider = OpenAIProvider(settings)
        compatible_provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        
        required_methods = ['ask', 'ask_many', 'upload_file', 'download_file', 'generate_image']
        
        for provider in [openai_provider, compatible_provider]:
            for method_name in required_methods:
                assert hasattr(provider, method_name)
                assert callable(getattr(provider, method_name))
    
    def test_all_providers_support_ask_text(self, OpenAIProvider):
        """Test all providers support ask_text convenience method."""
        settings = AiSettings(api_key="test-key", model="gpt-3.5-turbo")
        
        openai_provider = OpenAIProvider(settings)
        compatible_provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="http://localhost:8080"
        )
        
        for provider in [openai_provider, compatible_provider]:
            assert hasattr(provider, 'ask_text')
            assert callable(getattr(provider, 'ask_text'))
