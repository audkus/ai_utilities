"""Integration test for main.py to ensure real model usage works."""

import os
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.integration

def test_main_uses_real_models():
    """Test that main.py uses real OpenAI models, not test models."""
    # Patch the SDK boundary function to avoid requiring openai package
    with patch('ai_utilities.providers.openai_provider._create_openai_sdk_client') as mock_create_client, \
         patch.dict(os.environ, {'AI_API_KEY': 'test-key'}, clear=True):
        
        # Mock the OpenAI client and response with proper string content
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"  # String, not MagicMock
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        # Import and run main with mocked API
        from ai_utilities import create_client
        
        # Test that create_client with real model works
        client = create_client(model="gpt-4")
        
        # Verify the client was initialized with real model
        assert client.settings.model == "gpt-4"
        
        # Test that the model flows through to the API call
        response = client.ask("test prompt")
        assert response == "Test response"
        
        # Verify the SDK client was created (without model parameter)
        mock_create_client.assert_called_once()
        call_kwargs = mock_create_client.call_args[1]
        assert 'api_key' in call_kwargs
        assert 'base_url' in call_kwargs
        assert 'timeout' in call_kwargs
        assert 'model' not in call_kwargs  # Model is passed to API call, not client creation
        
        # Verify the API call was made with the correct model
        mock_client.chat.completions.create.assert_called()
        api_call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert api_call_kwargs.get('model') == 'gpt-4'

def test_create_client_vs_aiclient_model_difference():
    """Test the difference between create_client and AiClient for model selection."""
    from ai_utilities import create_client
    from ai_utilities.client import AiSettings
    
    # Patch the SDK boundary function to avoid requiring openai package
    with patch('ai_utilities.providers.openai_provider._create_openai_sdk_client') as mock_create_client, \
         patch.dict(os.environ, {'AI_API_KEY': 'test-key-for-testing'}, clear=True):
        
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        # create_client should allow specifying real models
        client_with_real_model = create_client(model="gpt-4", api_key="test-key-for-testing")
        assert client_with_real_model.settings.model == "gpt-4"
        
        # Test that the model flows through to the API call
        response = client_with_real_model.ask("test prompt")
        assert response == "Test response"
        
        # Verify the SDK client was created (without model parameter)
        mock_create_client.assert_called_once()
        call_kwargs = mock_create_client.call_args[1]
        assert 'api_key' in call_kwargs
        assert 'base_url' in call_kwargs
        assert 'timeout' in call_kwargs
        assert 'model' not in call_kwargs  # Model is passed to API call, not client creation
        
        # Verify the API call was made with the correct model
        mock_client.chat.completions.create.assert_called()
        api_call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert api_call_kwargs.get('model') == 'gpt-4'
    
    # AiSettings without parameters uses model from environment or default
    with patch.dict(os.environ, {}, clear=True):  # Clear environment to test default behavior
        settings_default = AiSettings()
        # In current implementation, model defaults to None when no environment variable
        assert settings_default.model is None
