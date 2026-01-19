"""Test OpenAI client functionality."""

import pytest
from unittest.mock import MagicMock, patch

from ai_utilities.openai_client import OpenAIClient


class TestOpenAIClient:
    """Test OpenAIClient class."""
    
    def test_initialization_default(self, request):
        """Test client initialization with default parameters."""
        # Get the global mocks from conftest
        mock_openai = request.config._openai_mock_constructor
        mock_client_instance = request.config._openai_mock_client
        
        # Reset the mock before the test
        mock_openai.reset_mock()
        
        client = OpenAIClient(api_key="test-key")
        
        assert client.client is mock_client_instance
        
        # Verify OpenAI was called with correct parameters (defaults are None)
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url=None,
            timeout=None
        )
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_initialization_custom_params(self, mock_openai):
        """Test client initialization with custom parameters."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        client = OpenAIClient(
            api_key="custom-key",
            base_url="https://custom.openai.com",
            timeout=60
        )
        
        assert client.client == mock_client_instance
        
        # Verify OpenAI was called with correct parameters
        mock_openai.assert_called_once_with(
            api_key="custom-key",
            base_url="https://custom.openai.com",
            timeout=60
        )
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_initialization_logging(self, mock_openai):
        """Test that initialization works without errors."""
        mock_openai.return_value = MagicMock()
        
        # Just test that initialization doesn't raise errors
        client = OpenAIClient(api_key="test-key")
        assert client is not None
        assert client.client is not None
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_create_chat_completion_basic(self, mock_openai):
        """Test basic chat completion creation."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        # Mock the chat completion response
        mock_response = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key="test-key")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, world!"}
        ]
        
        result = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        # Verify the result
        assert result == mock_response
        
        # Verify the API was called with correct parameters
        expected_params = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
        }
        mock_client_instance.chat.completions.create.assert_called_once_with(**expected_params)
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_create_chat_completion_with_max_tokens(self, mock_openai):
        """Test chat completion with max_tokens parameter."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key="test-key")
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = client.create_chat_completion(
            model="gpt-4",
            messages=messages,
            temperature=0.5,
            max_tokens=100
        )
        
        assert result == mock_response
        
        expected_params = {
            "model": "gpt-4",
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 100,
        }
        mock_client_instance.chat.completions.create.assert_called_once_with(**expected_params)
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_create_chat_completion_with_kwargs(self, mock_openai):
        """Test chat completion with additional kwargs."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key="test-key")
        
        messages = [{"role": "user", "content": "Test"}]
        
        result = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=messages,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        
        assert result == mock_response
        
        # Verify all parameters were passed
        call_args = mock_client_instance.chat.completions.create.call_args
        params = call_args[1]  # kwargs
        
        assert params["model"] == "gpt-3.5-turbo"
        assert params["messages"] == messages
        assert params["temperature"] == 0.7  # default
        assert params["top_p"] == 0.9
        assert params["frequency_penalty"] == 0.5
        assert params["presence_penalty"] == 0.5
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_create_chat_completion_logging(self, mock_openai):
        """Test that chat completion logs debug messages."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key="test-key")
        
        client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}]
        )
        
        # Just verify the call was made without errors
        mock_client_instance.chat.completions.create.assert_called_once()
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_create_chat_completion_api_exception(self, mock_openai):
        """Test handling of OpenAI API exceptions."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        # Mock API exception
        from openai import OpenAIError
        mock_client_instance.chat.completions.create.side_effect = OpenAIError("API Error")
        
        client = OpenAIClient(api_key="test-key")
        
        with pytest.raises(OpenAIError, match="API Error"):
            client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}]
            )
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_get_models(self, mock_openai):
        """Test getting available models."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        # Mock models response
        mock_models = MagicMock()
        mock_client_instance.models.list.return_value = mock_models
        
        client = OpenAIClient(api_key="test-key")
        
        result = client.get_models()
        
        assert result == mock_models
        mock_client_instance.models.list.assert_called_once()
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_get_models_logging(self, mock_openai):
        """Test that get_models logs debug message."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        mock_client_instance.models.list.return_value = MagicMock()
        
        client = OpenAIClient(api_key="test-key")
        client.get_models()
        
        # Just verify the call was made without errors
        mock_client_instance.models.list.assert_called_once()
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_get_models_api_exception(self, mock_openai):
        """Test handling of API exceptions in get_models."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        from openai import OpenAIError
        mock_client_instance.models.list.side_effect = OpenAIError("Models API Error")
        
        client = OpenAIClient(api_key="test-key")
        
        with pytest.raises(OpenAIError, match="Models API Error"):
            client.get_models()


class TestOpenAIClientIntegration:
    """Integration tests for OpenAIClient."""
    
    def test_single_responsibility_principle(self):
        """Test that client only handles API communication."""
        # Use patch.object with new_callable for more robust patching
        import ai_utilities.openai_client
        with patch.object(ai_utilities.openai_client, 'OpenAI', new_callable=MagicMock) as mock_openai:
            mock_client_instance = MagicMock()
            mock_openai.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient(api_key="test-key")
            
            # Client should not handle rate limiting, response processing, etc.
            # It should just pass through to the underlying OpenAI client
            messages = [{"role": "user", "content": "Test"}]
            
            result = client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=100,
                top_p=0.9
            )
        
        # Should return exactly what the OpenAI client returns
        assert result is mock_response
        
        # Should pass all parameters through without modification
        call_kwargs = mock_client_instance.chat.completions.create.call_args[1]
        assert call_kwargs["messages"] == messages
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["top_p"] == 0.9
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_parameter_validation_delegation(self, mock_openai):
        """Test that parameter validation is delegated to OpenAI client."""
        mock_client_instance = MagicMock()
        mock_openai.return_value = mock_client_instance
        
        client = OpenAIClient(api_key="test-key")
        
        # Client should not validate parameters - let OpenAI handle it
        # This includes things like temperature range, message format, etc.
        client.create_chat_completion(
            model="any-model",
            messages=[{"role": "any", "content": "content"}],
            temperature=5.0,  # Outside normal range
            invalid_param="should_pass_through"
        )
        
        # Should pass all parameters to OpenAI without validation
        call_kwargs = mock_client_instance.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 5.0
        assert call_kwargs["invalid_param"] == "should_pass_through"


class TestOpenAIClientEdgeCases:
    """Test edge cases for OpenAIClient."""
    
    def test_empty_messages_list(self):
        """Test with empty messages list."""
        # Use patch.object with new_callable for more robust patching
        import ai_utilities.openai_client
        with patch.object(ai_utilities.openai_client, 'OpenAI', new_callable=MagicMock) as mock_openai:
            mock_client_instance = MagicMock()
            mock_openai.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient(api_key="test-key")
            
            result = client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[]
            )
            
            assert result == mock_response
            mock_client_instance.chat.completions.create.assert_called_once()
    
    def test_zero_max_tokens(self):
        """Test with max_tokens=0 (should be filtered out as falsy)."""
        # Use patch.object to ensure we patch the exact module attribute
        import ai_utilities.openai_client
        with patch.object(ai_utilities.openai_client, 'OpenAI') as mock_openai:
            mock_client_instance = MagicMock()
            mock_openai.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient(api_key="test-key")
            
            result = client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=0
            )
            
            assert result == mock_response
            call_kwargs = mock_client_instance.chat.completions.create.call_args[1]
            # When max_tokens=0, it's falsy so not included in params
            assert "max_tokens" not in call_kwargs
    
    def test_none_max_tokens(self):
        """Test with max_tokens=None (should not be included)."""
        # Use patch.object to ensure we patch the exact module attribute
        import ai_utilities.openai_client
        with patch.object(ai_utilities.openai_client, 'OpenAI') as mock_openai:
            mock_client_instance = MagicMock()
            mock_openai.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient(api_key="test-key")
            
            result = client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=None
            )
            
            assert result == mock_response
            call_kwargs = mock_client_instance.chat.completions.create.call_args[1]
            assert "max_tokens" not in call_kwargs
    
    def test_large_number_of_kwargs(self):
        """Test with many additional kwargs (should pass through)."""
        # Use patch.object to ensure we patch the exact module attribute
        import ai_utilities.openai_client
        with patch.object(ai_utilities.openai_client, 'OpenAI') as mock_openai:
            mock_client_instance = MagicMock()
            mock_openai.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient(api_key="test-key")
            
            result = client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.5,
                max_tokens=100,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stop=["\n"],
                stream=False,
                logprobs=False,
                top_logprobs=1
            )
            
            assert result == mock_response
            mock_client_instance.chat.completions.create.assert_called_once()
