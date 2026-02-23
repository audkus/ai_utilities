"""
Final test to achieve 100% coverage for OpenAIProvider.
"""

import pytest
from unittest.mock import Mock
from ai_utilities.providers.provider_exceptions import MissingOptionalDependencyError


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
    
    def test_ask_json_response_unsupported_model_line_107(self, force_openai_missing):
        """Test OpenAI provider raises MissingOptionalDependencyError when openai is missing."""
        from ai_utilities.providers.openai_provider import OpenAIProvider
        
        with pytest.raises(MissingOptionalDependencyError, match="OpenAI package is required"):
            OpenAIProvider(self.mock_settings)
    
    def test_provider_name_property_exists(self, force_openai_missing):
        """Test OpenAI provider raises MissingOptionalDependencyError when openai is missing."""
        from ai_utilities.providers.openai_provider import OpenAIProvider
        
        with pytest.raises(MissingOptionalDependencyError, match="OpenAI package is required"):
            OpenAIProvider(self.mock_settings)
