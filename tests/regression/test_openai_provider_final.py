"""
Final test to achieve 100% coverage for OpenAIProvider.
"""

import pytest
from unittest.mock import Mock


class TestOpenAIProviderFinal:
    """Final tests to achieve 100% coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_settings = Mock()
        self.mock_settings.api_key = "test-api-key"
        self.mock_settings.base_url = "https://api.openai.com/v1"
        self.mock_settings.timeout = 30
        self.mock_settings.model = "text-davinci-003"  # Unsupported model for JSON
        self.mock_settings.temperature = 0.7
        self.mock_settings.max_tokens = 1000
    
    def test_ask_json_response_unsupported_model_line_107(self, openai_mocks, openai_provider_mod):
        """Test ask method with JSON response using unsupported model - covers line 107."""
        constructor_mock, client_mock = openai_mocks
        
        # Mock OpenAI client response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = 'Here is some text with {"json": "content"} embedded'
        mock_response.choices = [mock_choice]
        client_mock.chat.completions.create.return_value = mock_response
        
        provider = openai_provider_mod.OpenAIProvider(self.mock_settings)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call does NOT include JSON response format
        client_mock.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="text-davinci-003",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Should extract JSON from text - this covers line 107
        assert result == {"json": "content"}
    
    def test_provider_name_property_exists(self, openai_mocks, openai_provider_mod):
        """Test that provider has provider_name attribute."""
        constructor_mock, client_mock = openai_mocks
        
        provider = openai_provider_mod.OpenAIProvider(self.mock_settings)
        
        # Test that provider_name is read-only and returns "openai"
        assert provider.provider_name == "openai"
        
        # Verify it's a property, not a settable attribute
        with pytest.raises(AttributeError):
            provider.provider_name = "custom_provider"
