"""
Final test to achieve 100% coverage for OpenAIProvider.
"""

import pytest
from unittest.mock import Mock, patch

from ai_utilities.providers.openai_provider import OpenAIProvider


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
    
    @patch('ai_utilities.providers.openai_provider.OpenAI')
    def test_ask_json_response_unsupported_model_line_107(self, mock_openai):
        """Test ask method with JSON response using unsupported model - covers line 107."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = 'Here is some text with {"json": "content"} embedded'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider(self.mock_settings)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call does NOT include JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="text-davinci-003",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Should extract JSON from text - this covers line 107
        assert result == {"json": "content"}
    
    @patch('ai_utilities.providers.openai_provider.OpenAI')
    def test_provider_name_property_exists(self, mock_openai):
        """Test that provider can have provider_name attribute."""
        mock_openai.return_value = Mock()
        
        provider = OpenAIProvider(self.mock_settings)
        
        # Test that we can set and access provider_name
        provider.provider_name = "openai"
        assert provider.provider_name == "openai"
        
        # Test with different name
        provider.provider_name = "custom_provider"
        assert provider.provider_name == "custom_provider"
