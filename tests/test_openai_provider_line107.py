"""
Test to cover line 107 in OpenAIProvider - the JSON extraction path.
"""

import pytest
from unittest.mock import Mock, patch

from ai_utilities.providers.openai_provider import OpenAIProvider


class TestOpenAIProviderLine107:
    """Test to cover line 107 specifically."""
    
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
    def test_line107_json_extraction_path(self, mock_openai):
        """Test that line 107 is executed - JSON extraction for unsupported models."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = 'Response with {"key": "value"} embedded'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider(self.mock_settings)
        
        # This should execute line 107: return self._extract_json(result)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify the result
        assert result == {"key": "value"}
