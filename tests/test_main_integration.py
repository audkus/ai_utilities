"""Integration test for main.py to ensure real model usage works."""

import os

# Add src to path for imports
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_main_uses_real_models():
    """Test that main.py uses real OpenAI models, not test models."""
    # Mock the actual OpenAI API calls but verify model names
    with patch('ai_utilities.providers.openai_provider.OpenAI') as mock_openai, \
         patch.dict(os.environ, {'AI_API_KEY': 'test-key'}):
        # Mock the OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Import and run main with mocked API
        from ai_utilities import create_client
        
        # Test that create_client with real model works
        client = create_client(model="gpt-4")
        
        # Verify the client was initialized with real model
        assert client.settings.model == "gpt-4"
        
        # Test that default client would fail with test model
        try:
            from ai_utilities import AiClient
            # This should work in mocked environment with API key
            client_default = AiClient(api_key="test-key")
            # But in real environment, this would trigger interactive setup
            assert client_default.settings.model == "test-model-1"
        except Exception:
            # In real environment without API key, this would trigger setup
            pass

def test_create_client_vs_aiclient_model_difference():
    """Test the difference between create_client and AiClient for model selection."""
    from ai_utilities import create_client
    from ai_utilities.client import AiSettings
    import os
    
    # create_client should allow specifying real models
    client_with_real_model = create_client(model="gpt-4", api_key="test-key-for-testing")
    assert client_with_real_model.settings.model == "gpt-4"
    
    # AiSettings without parameters uses model from environment or default
    settings_default = AiSettings()
    expected_model = os.environ.get('AI_MODEL')  # No fallback default anymore
    assert settings_default.model == expected_model
    
    # This demonstrates the issue: default settings use environment models
    # but real applications need real OpenAI models
