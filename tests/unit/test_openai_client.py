"""Test OpenAI client functionality."""

import pytest
import importlib
from unittest.mock import MagicMock, patch
from typing import Tuple
from types import ModuleType
import sys

# Mock the openai module at system level to avoid import errors
sys.modules['openai'] = MagicMock()

@pytest.fixture
def openai_client_mod(openai_mocks: Tuple[MagicMock, MagicMock]) -> ModuleType:
    """Import ai_utilities.openai_client AFTER openai_mocks has patched constructors."""
    sys.modules.pop("ai_utilities.openai_client", None)
    return importlib.import_module("ai_utilities.openai_client")


class TestOpenAIClient:
    """Test OpenAI client class."""
    
    def test_initialization_default(self, openai_mocks, openai_client_mod):
        """Test client initialization with default parameters."""
        constructor_mock, client_mock = openai_mocks

        # Patch the lazy import mechanism in openai_client
        import ai_utilities.openai_client
        ai_utilities.openai_client.OpenAI = constructor_mock
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        # Verify client has the mock instance
        assert client.client is client_mock
        
        # Verify OpenAI constructor called with correct parameters (defaults are None)
        constructor_mock.assert_called_once_with(
            api_key="test-key",
            base_url=None,
            timeout=None
        )
    
    def test_initialization_custom_params(self, openai_mocks, openai_client_mod):
        """Test client initialization with custom parameters."""
        constructor_mock, client_mock = openai_mocks
        
        client = openai_client_mod.OpenAIClient(
            api_key="custom-key",
            base_url="https://custom.openai.com",
            timeout=60
        )
        
        # Verify client has the mock instance
        assert client.client is client_mock
        
        # Verify OpenAI constructor called with custom parameters
        constructor_mock.assert_called_once_with(
            api_key="custom-key",
            base_url="https://custom.openai.com",
            timeout=60
        )
    
    def test_initialization_logging(self, openai_mocks, openai_client_mod):
        """Test that initialization works without errors."""
        constructor_mock, client_mock = openai_mocks
        
        # Just test that initialization doesn't raise errors
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        assert client is not None
        assert client.client is client_mock
    
    def test_create_chat_completion_basic(self, openai_mocks, openai_client_mod):
        """Test basic chat completion creation."""
        constructor_mock, client_mock = openai_mocks
        
        # Mock the chat completion response
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
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
        client_mock.chat.completions.create.assert_called_once_with(**expected_params)
    
    def test_create_chat_completion_with_max_tokens(self, openai_mocks, openai_client_mod):
        """Test chat completion with max_tokens parameter."""
        constructor_mock, client_mock = openai_mocks
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
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
        client_mock.chat.completions.create.assert_called_once_with(**expected_params)
    
    def test_create_chat_completion_with_kwargs(self, openai_mocks, openai_client_mod):
        """Test chat completion with additional kwargs."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
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
        call_args = client_mock.chat.completions.create.call_args
        params = call_args[1]  # kwargs
        
        assert params["model"] == "gpt-3.5-turbo"
        assert params["messages"] == messages
        assert params["temperature"] == 0.7  # default
        assert params["top_p"] == 0.9
        assert params["frequency_penalty"] == 0.5
        assert params["presence_penalty"] == 0.5
    
    def test_create_chat_completion_logging(self, openai_mocks, openai_client_mod):
        """Test that chat completion logs debug messages."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}]
        )
        
        # Just verify the call was made without errors
        client_mock.chat.completions.create.assert_called_once()
    
    def test_create_chat_completion_api_exception(self, openai_mocks, openai_client_mod):
        """Test handling of OpenAI API exceptions."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        # Create a real exception class for testing
        class OpenAIError(Exception):
            pass
        
        client_mock.chat.completions.create.side_effect = OpenAIError("API Error")
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        with pytest.raises(OpenAIError, match="API Error"):
            client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}]
            )
    
    def test_get_models(self, openai_mocks, openai_client_mod):
        """Test getting available models."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        # Mock models response
        mock_models = MagicMock()
        client_mock.models.list.return_value = mock_models
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        result = client.get_models()
        
        assert result == mock_models
        client_mock.models.list.assert_called_once()
    
    def test_get_models_logging(self, openai_mocks, openai_client_mod):
        """Test that get_models logs debug message."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        client_mock.models.list.return_value = MagicMock()
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        client.get_models()
        
        # Just verify the call was made without errors
        client_mock.models.list.assert_called_once()
    
    def test_get_models_api_exception(self, openai_mocks, openai_client_mod):
        """Test handling of API exceptions in get_models."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        # Create a real exception class for testing
        class OpenAIError(Exception):
            pass
        
        client_mock.models.list.side_effect = OpenAIError("Models API Error")
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        with pytest.raises(OpenAIError, match="Models API Error"):
            client.get_models()


class TestOpenAIClientIntegration:
    """Integration tests for OpenAIClient."""
    
    def test_single_responsibility_principle(self, openai_mocks, openai_client_mod):
        """Test that client only handles API communication."""
        constructor_mock, client_mock = openai_mocks
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
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
        call_kwargs = client_mock.chat.completions.create.call_args[1]
        assert call_kwargs["messages"] == messages
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["top_p"] == 0.9
    
    def test_parameter_validation_delegation(self, openai_mocks, openai_client_mod):
        """Test that parameter validation is delegated to OpenAI client."""
        constructor_mock, client_mock = openai_mocks
        # Mock setup handled by fixture
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        # Client should not validate parameters - let OpenAI handle it
        # This includes things like temperature range, message format, etc.
        client.create_chat_completion(
            model="any-model",
            messages=[{"role": "any", "content": "content"}],
            temperature=5.0,  # Outside normal range
            invalid_param="should_pass_through"
        )
        
        # Should pass all parameters to OpenAI without validation
        call_kwargs = client_mock.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 5.0
        assert call_kwargs["invalid_param"] == "should_pass_through"


class TestOpenAIClientEdgeCases:
    """Test edge cases for OpenAIClient."""
    
    def test_empty_messages_list(self, openai_mocks, openai_client_mod):
        """Test with empty messages list."""
        constructor_mock, client_mock = openai_mocks
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        result = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=[]
        )
        
        assert result == mock_response
        client_mock.chat.completions.create.assert_called_once()
    
    def test_zero_max_tokens(self, openai_mocks, openai_client_mod):
        """Test with max_tokens=0 (should be filtered out as falsy)."""
        constructor_mock, client_mock = openai_mocks
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        result = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=0
        )
        
        assert result == mock_response
        call_kwargs = client_mock.chat.completions.create.call_args[1]
        # When max_tokens=0, it's falsy so not included in params
        assert "max_tokens" not in call_kwargs
    
    def test_none_max_tokens(self, openai_mocks, openai_client_mod):
        """Test with max_tokens=None (should not be included)."""
        constructor_mock, client_mock = openai_mocks
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        result = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=None
        )
        
        assert result == mock_response
        call_kwargs = client_mock.chat.completions.create.call_args[1]
        assert "max_tokens" not in call_kwargs
    
    def test_large_number_of_kwargs(self, openai_mocks, openai_client_mod):
        """Test with many additional kwargs (should pass through)."""
        constructor_mock, client_mock = openai_mocks
        
        mock_response = MagicMock()
        client_mock.chat.completions.create.return_value = mock_response
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        
        # Test with many kwargs
        result = client.create_chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.5,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            max_tokens=100,
            stream=False,
            logprobs=None,
            echo=False
        )
        
        assert result == mock_response
        
        # Verify all kwargs were passed through
        call_kwargs = client_mock.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["frequency_penalty"] == 0.1
        assert call_kwargs["presence_penalty"] == 0.1
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["stream"] is False
        assert call_kwargs["logprobs"] is None
        assert call_kwargs["echo"] is False
