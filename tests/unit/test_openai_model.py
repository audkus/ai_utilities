"""Tests for openai_model.py module."""

import pytest
from unittest.mock import patch, MagicMock
from configparser import ConfigParser

from ai_utilities.openai_model import OpenAIModel
from ai_utilities.exceptions import RateLimitExceededError


class TestOpenAIModel:
    """Test OpenAIModel class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = ConfigParser()
        config.add_section('gpt-3.5-turbo')
        config.set('gpt-3.5-turbo', 'requests_per_minute', '60')
        config.set('gpt-3.5-turbo', 'tokens_per_minute', '40000')
        config.set('gpt-3.5-turbo', 'tokens_per_day', '100000')
        config.add_section('gpt-4')
        config.set('gpt-4', 'requests_per_minute', '60')
        config.set('gpt-4', 'tokens_per_minute', '40000')
        config.set('gpt-4', 'tokens_per_day', '100000')
        return config
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.logger')
    def test_initialization(self, mock_logger, mock_rate_limiter, mock_token_counter, 
                           mock_response_processor, mock_openai_client, mock_config):
        """Test OpenAIModel initialization."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-3.5-turbo",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        # Verify components are initialized
        assert model.api_client == mock_client_instance
        assert model.response_processor == mock_processor_instance
        assert model.token_counter == mock_counter_instance
        assert model.rate_limiter == mock_limiter_instance
        assert model.model == "gpt-3.5-turbo"
        
        # Verify OpenAI client was initialized correctly
        mock_openai_client.assert_called_once_with(api_key="test-key")
        
        # Verify rate limiter was initialized with correct parameters
        mock_rate_limiter.assert_called_once_with(
            module_name="gpt-3.5-turbo",
            rpm=60,
            tpm=40000,
            tpd=100000,
            config_path="/path/to/config"
        )
        
        # Verify rate limiter timer was started
        mock_limiter_instance.start_reset_timer.assert_called_once()
        
        # Verify debug logging
        mock_logger.debug.assert_called_once_with("OpenAIModel initialized with model: gpt-3.5-turbo")
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_initialization_different_model(self, mock_rate_limiter, mock_token_counter, 
                                          mock_response_processor, mock_openai_client):
        """Test initialization with different model configuration."""
        config = ConfigParser()
        config.add_section('gpt-4')
        config.set('gpt-4', 'requests_per_minute', '30')
        config.set('gpt-4', 'tokens_per_minute', '80000')
        config.set('gpt-4', 'tokens_per_day', '200000')
        
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-4",
            config=config,
            config_path="/path/to/config"
        )
        
        # Verify rate limiter was initialized with correct parameters for gpt-4
        mock_rate_limiter.assert_called_once_with(
            module_name="gpt-4",
            rpm=30,
            tpm=80000,
            tpd=200000,
            config_path="/path/to/config"
        )
        
        assert model.model == "gpt-4"
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.logger')
    def test_ask_ai_success_text_format(self, mock_logger, mock_rate_limiter, mock_token_counter,
                                       mock_response_processor, mock_openai_client, mock_config):
        """Test successful AI interaction with text format."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup method behaviors
        mock_counter_instance.count_tokens_for_model.return_value = 10
        mock_limiter_instance.can_proceed.return_value = True
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  This is a test response  "
        mock_client_instance.create_chat_completion.return_value = mock_response
        
        # Mock response processing
        mock_processor_instance.format_response.return_value = "This is a test response"
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-3.5-turbo",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        result = model.ask_ai("Hello, world!", return_format="text")
        
        # Verify token counting
        mock_counter_instance.count_tokens_for_model.assert_called_once_with("Hello, world!", "gpt-3.5-turbo")
        
        # Verify rate limiting check
        mock_limiter_instance.can_proceed.assert_called_once_with(10)
        
        # Verify API call
        mock_client_instance.create_chat_completion.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, world!"}]
        )
        
        # Verify response processing
        mock_processor_instance.format_response.assert_called_once_with(
            "This is a test response", "text"
        )
        
        # Verify final result
        assert result == "This is a test response"
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.logger')
    def test_ask_ai_success_json_format(self, mock_logger, mock_rate_limiter, mock_token_counter,
                                       mock_response_processor, mock_openai_client, mock_config):
        """Test successful AI interaction with JSON format."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup method behaviors
        mock_counter_instance.count_tokens_for_model.return_value = 15
        mock_limiter_instance.can_proceed.return_value = True
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "success"}'
        mock_client_instance.create_chat_completion.return_value = mock_response
        
        # Mock response processing
        mock_processor_instance.format_response.return_value = '{"result": "success"}'
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-4",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        result = model.ask_ai("Get JSON data", return_format="json")
        
        # Verify response processing with JSON format
        mock_processor_instance.format_response.assert_called_once_with(
            '{"result": "success"}', "json"
        )
        
        assert result == '{"result": "success"}'
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.logger')
    def test_ask_ai_rate_limit_exceeded(self, mock_logger, mock_rate_limiter, mock_token_counter,
                                       mock_response_processor, mock_openai_client, mock_config):
        """Test rate limit exceeded scenario."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup rate limit exceeded
        mock_counter_instance.count_tokens_for_model.return_value = 100
        mock_limiter_instance.can_proceed.return_value = False
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-3.5-turbo",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        # Should raise RateLimitExceededError
        with pytest.raises(RateLimitExceededError, match="Rate limit exceeded"):
            model.ask_ai("This will exceed rate limit")
        
        # Verify error logging
        mock_logger.error.assert_called_once_with("Rate limit exceeded")
        
        # Verify API was not called
        mock_client_instance.create_chat_completion.assert_not_called()
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_ask_ai_api_error(self, mock_rate_limiter, mock_token_counter,
                             mock_response_processor, mock_openai_client, mock_config):
        """Test handling of OpenAI API errors."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup behaviors
        mock_counter_instance.count_tokens_for_model.return_value = 10
        mock_limiter_instance.can_proceed.return_value = True
        
        # Mock API error
        from openai import OpenAIError
        mock_client_instance.create_chat_completion.side_effect = OpenAIError("API Error")
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-3.5-turbo",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        # Should propagate OpenAI error
        with pytest.raises(OpenAIError, match="API Error"):
            model.ask_ai("This will cause API error")


class TestOpenAIModelIntegration:
    """Integration tests for OpenAIModel composition."""
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_composition_pattern(self, mock_rate_limiter, mock_token_counter,
                                mock_response_processor, mock_openai_client):
        """Test that OpenAIModel properly uses composition pattern."""
        config = ConfigParser()
        config.add_section('test-model')
        config.set('test-model', 'requests_per_minute', '10')
        config.set('test-model', 'tokens_per_minute', '1000')
        config.set('test-model', 'tokens_per_day', '10000')
        
        # Create model instance
        model = OpenAIModel(
            api_key="test-key",
            model="test-model",
            config=config,
            config_path="/path/to/config"
        )
        
        # Verify all components are composed
        assert hasattr(model, 'api_client')
        assert hasattr(model, 'response_processor')
        assert hasattr(model, 'token_counter')
        assert hasattr(model, 'rate_limiter')
        
        # Verify components are properly initialized
        mock_openai_client.assert_called_once()
        mock_response_processor.assert_called_once()
        mock_token_counter.assert_called_once()
        mock_rate_limiter.assert_called_once()
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_single_responsibility_coordination(self, mock_rate_limiter, mock_token_counter,
                                               mock_response_processor, mock_openai_client):
        """Test that OpenAIModel coordinates between single-responsibility components."""
        config = ConfigParser()
        config.add_section('test-model')
        config.set('test-model', 'requests_per_minute', '10')
        config.set('test-model', 'tokens_per_minute', '1000')
        config.set('test-model', 'tokens_per_day', '10000')
        
        # Setup component mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup component behaviors
        mock_counter_instance.count_tokens_for_model.return_value = 25
        mock_limiter_instance.can_proceed.return_value = True
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Processed response"
        mock_client_instance.create_chat_completion.return_value = mock_response
        
        mock_processor_instance.format_response.return_value = "Final formatted response"
        
        model = OpenAIModel(
            api_key="test-key",
            model="test-model",
            config=config,
            config_path="/path/to/config"
        )
        
        result = model.ask_ai("Test prompt", return_format="text")
        
        # Verify coordination flow:
        # 1. Token counter was used for rate limiting
        mock_counter_instance.count_tokens_for_model.assert_called_once_with("Test prompt", "test-model")
        
        # 2. Rate limiter was checked
        mock_limiter_instance.can_proceed.assert_called_once_with(25)
        
        # 3. API client was used for communication
        mock_client_instance.create_chat_completion.assert_called_once()
        
        # 4. Response processor was used for formatting
        mock_processor_instance.format_response.assert_called_once_with("Processed response", "text")
        
        # Verify final result
        assert result == "Final formatted response"


class TestOpenAIModelEdgeCases:
    """Edge case tests for OpenAIModel."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = ConfigParser()
        config.add_section('gpt-3.5-turbo')
        config.set('gpt-3.5-turbo', 'requests_per_minute', '60')
        config.set('gpt-3.5-turbo', 'tokens_per_minute', '40000')
        config.set('gpt-3.5-turbo', 'tokens_per_day', '100000')
        config.add_section('gpt-4')
        config.set('gpt-4', 'requests_per_minute', '60')
        config.set('gpt-4', 'tokens_per_minute', '40000')
        config.set('gpt-4', 'tokens_per_day', '100000')
        return config
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_empty_prompt(self, mock_rate_limiter, mock_token_counter,
                         mock_response_processor, mock_openai_client, mock_config):
        """Test handling of empty prompt."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup behaviors
        mock_counter_instance.count_tokens_for_model.return_value = 0
        mock_limiter_instance.can_proceed.return_value = True
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_client_instance.create_chat_completion.return_value = mock_response
        
        mock_processor_instance.format_response.return_value = ""
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-3.5-turbo",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        result = model.ask_ai("", return_format="text")
        
        # Should handle empty prompt gracefully
        assert result == ""
        mock_counter_instance.count_tokens_for_model.assert_called_once_with("", "gpt-3.5-turbo")
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_large_token_count(self, mock_rate_limiter, mock_token_counter,
                              mock_response_processor, mock_openai_client, mock_config):
        """Test handling of large token count."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = MagicMock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = MagicMock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup large token count
        mock_counter_instance.count_tokens_for_model.return_value = 10000
        mock_limiter_instance.can_proceed.return_value = True
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Large response"
        mock_client_instance.create_chat_completion.return_value = mock_response
        
        mock_processor_instance.format_response.return_value = "Large response"
        
        model = OpenAIModel(
            api_key="test-key",
            model="gpt-4",
            config=mock_config,
            config_path="/path/to/config"
        )
        
        result = model.ask_ai("A" * 10000, return_format="text")  # Very long prompt
        
        # Should handle large token count
        mock_limiter_instance.can_proceed.assert_called_once_with(10000)
        assert result == "Large response"
    
