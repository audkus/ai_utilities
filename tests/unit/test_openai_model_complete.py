"""
Comprehensive tests for OpenAIModel to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from configparser import ConfigParser
import logging

from ai_utilities.openai_model import OpenAIModel
from ai_utilities.exceptions import RateLimitExceededError
from ai_utilities.error_codes import ERROR_RATE_LIMIT_EXCEEDED


class TestOpenAIModelComplete:
    """Comprehensive test suite for OpenAIModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigParser()
        self.config.add_section('test-model')
        self.config.set('test-model', 'requests_per_minute', '60')
        self.config.set('test-model', 'tokens_per_minute', '90000')
        self.config.set('test-model', 'tokens_per_day', '1000000')
        
        self.api_key = "test-api-key"
        self.model = "test-model"
        self.config_path = "/test/config/path"
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_initialization_success(self, mock_token_counter, mock_response_processor, 
                                   mock_rate_limiter, mock_openai_client):
        """Test successful initialization of OpenAIModel."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        # Create model
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        
        # Verify components are initialized
        mock_openai_client.assert_called_once_with(api_key=self.api_key)
        mock_response_processor.assert_called_once()
        mock_token_counter.assert_called_once()
        mock_rate_limiter.assert_called_once_with(
            module_name=self.model,
            rpm=60,
            tpm=90000,
            tpd=1000000,
            config_path=self.config_path
        )
        
        # Verify rate limiter is started
        mock_rate_limiter_instance.start_reset_timer.assert_called_once()
        
        # Verify model attributes
        assert model.model == self.model
        assert model.api_client is not None
        assert model.response_processor is not None
        assert model.token_counter is not None
        assert model.rate_limiter is not None
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_initialization_with_different_config_values(self, mock_token_counter, mock_response_processor, 
                                                        mock_rate_limiter, mock_openai_client):
        """Test initialization with different configuration values."""
        # Set different config values
        self.config.set('test-model', 'requests_per_minute', '120')
        self.config.set('test-model', 'tokens_per_minute', '180000')
        self.config.set('test-model', 'tokens_per_day', '2000000')
        
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        # Create model
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        
        # Verify rate limiter is called with correct values
        mock_rate_limiter.assert_called_once_with(
            module_name=self.model,
            rpm=120,
            tpm=180000,
            tpd=2000000,
            config_path=self.config_path
        )
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_ask_ai_rate_limit_exceeded(self, mock_token_counter, mock_response_processor, 
                                       mock_rate_limiter, mock_openai_client):
        """Test ask_ai when rate limit is exceeded."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.can_proceed.return_value = False
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        # Create model
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        
        # Test rate limit exceeded
        with pytest.raises(RateLimitExceededError) as exc_info:
            model.ask_ai("test prompt")
        
        assert str(ERROR_RATE_LIMIT_EXCEEDED) in str(exc_info.value)
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_ask_ai_successful_text_response(self, mock_token_counter, mock_response_processor, 
                                           mock_rate_limiter, mock_openai_client):
        """Test successful ask_ai with text response."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.can_proceed.return_value = True
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        mock_token_counter_instance = Mock()
        mock_token_counter_instance.count_tokens_for_model.return_value = 10
        mock_token_counter.return_value = mock_token_counter_instance
        
        mock_response_processor_instance = Mock()
        mock_response_processor_instance.format_response.return_value = "processed response"
        mock_response_processor.return_value = mock_response_processor_instance
        
        mock_api_client_instance = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "raw response"
        mock_response.choices = [mock_choice]
        mock_api_client_instance.create_chat_completion.return_value = mock_response
        mock_openai_client.return_value = mock_api_client_instance
        
        # Create model and test
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        result = model.ask_ai("test prompt")
        
        # Verify calls
        mock_token_counter_instance.count_tokens_for_model.assert_called_once_with("test prompt", self.model)
        mock_rate_limiter_instance.can_proceed.assert_called_once_with(10)
        mock_api_client_instance.create_chat_completion.assert_called_once_with(
            model=self.model,
            messages=[{"role": "user", "content": "test prompt"}]
        )
        mock_response_processor_instance.format_response.assert_called_once_with("raw response", "text")
        
        # Contract: verify model was called and returned a result (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_ask_ai_successful_json_response(self, mock_token_counter, mock_response_processor, 
                                           mock_rate_limiter, mock_openai_client):
        """Test successful ask_ai with JSON response."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.can_proceed.return_value = True
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        mock_token_counter_instance = Mock()
        mock_token_counter_instance.count_tokens_for_model.return_value = 15
        mock_token_counter.return_value = mock_token_counter_instance
        
        mock_response_processor_instance = Mock()
        mock_response_processor_instance.format_response.return_value = {"key": "value"}
        mock_response_processor.return_value = mock_response_processor_instance
        
        mock_api_client_instance = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "raw json response"
        mock_response.choices = [mock_choice]
        mock_api_client_instance.create_chat_completion.return_value = mock_response
        mock_openai_client.return_value = mock_api_client_instance
        
        # Create model and test
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        result = model.ask_ai("test prompt", return_format='json')
        
        # Verify JSON format is passed to response processor
        mock_response_processor_instance.format_response.assert_called_once_with("raw json response", "json")
        
        # Contract: verify model was called and returned a result (passthrough)
        assert result is not None
        assert isinstance(result, dict)  # Verify return type contract for JSON
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_ask_ai_with_empty_response(self, mock_token_counter, mock_response_processor, 
                                      mock_rate_limiter, mock_openai_client):
        """Test ask_ai with empty response from API."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.can_proceed.return_value = True
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        mock_token_counter_instance = Mock()
        mock_token_counter_instance.count_tokens_for_model.return_value = 5
        mock_token_counter.return_value = mock_token_counter_instance
        
        mock_response_processor_instance = Mock()
        mock_response_processor_instance.format_response.return_value = "processed empty"
        mock_response_processor.return_value = mock_response_processor_instance
        
        mock_api_client_instance = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = None  # Empty response
        mock_response.choices = [mock_choice]
        mock_api_client_instance.create_chat_completion.return_value = mock_response
        mock_openai_client.return_value = mock_api_client_instance
        
        # Create model and test
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        result = model.ask_ai("test prompt")
        
        # Verify empty response is handled (None becomes empty string after strip)
        mock_response_processor_instance.format_response.assert_called_once_with("", "text")
        
        # Contract: verify model was called and returned a result (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_ask_ai_with_whitespace_response(self, mock_token_counter, mock_response_processor, 
                                           mock_rate_limiter, mock_openai_client):
        """Test ask_ai with whitespace-only response."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.can_proceed.return_value = True
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        mock_token_counter_instance = Mock()
        mock_token_counter_instance.count_tokens_for_model.return_value = 8
        mock_token_counter.return_value = mock_token_counter_instance
        
        mock_response_processor_instance = Mock()
        mock_response_processor_instance.format_response.return_value = "processed whitespace"
        mock_response_processor.return_value = mock_response_processor_instance
        
        mock_api_client_instance = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "   \n\t  "  # Whitespace only
        mock_response.choices = [mock_choice]
        mock_api_client_instance.create_chat_completion.return_value = mock_response
        mock_openai_client.return_value = mock_api_client_instance
        
        # Create model and test
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        result = model.ask_ai("test prompt")
        
        # Verify whitespace response is stripped
        mock_response_processor_instance.format_response.assert_called_once_with("", "text")
        
        # Contract: verify model was called and returned a result (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.RateLimiter')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    def test_ask_ai_with_different_token_counts(self, mock_token_counter, mock_response_processor, 
                                             mock_rate_limiter, mock_openai_client):
        """Test ask_ai with different token counts."""
        # Configure mocks
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.can_proceed.return_value = True
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        mock_token_counter_instance = Mock()
        mock_token_counter_instance.count_tokens_for_model.return_value = 100  # High token count
        mock_token_counter.return_value = mock_token_counter_instance
        
        mock_response_processor_instance = Mock()
        mock_response_processor_instance.format_response.return_value = "processed"
        mock_response_processor.return_value = mock_response_processor_instance
        
        mock_api_client_instance = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "response"
        mock_response.choices = [mock_choice]
        mock_api_client_instance.create_chat_completion.return_value = mock_response
        mock_openai_client.return_value = mock_api_client_instance
        
        # Create model and test
        model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
        result = model.ask_ai("long prompt with many tokens")
        
        # Verify token count is passed to rate limiter
        mock_rate_limiter_instance.can_proceed.assert_called_once_with(100)
        
        # Contract: verify model was called and returned a result (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
    
    @patch('ai_utilities.openai_model.logger')
    def test_debug_logging_on_initialization(self, mock_logger):
        """Test that debug logging occurs during initialization."""
        with patch('ai_utilities.openai_model.OpenAIClient'), \
             patch('ai_utilities.openai_model.RateLimiter') as mock_rate_limiter, \
             patch('ai_utilities.openai_model.ResponseProcessor'), \
             patch('ai_utilities.openai_model.TokenCounter'):
            
            mock_rate_limiter_instance = Mock()
            mock_rate_limiter.return_value = mock_rate_limiter_instance
            
            # Create model
            model = OpenAIModel(self.api_key, self.model, self.config, self.config_path)
            
            # Verify debug log message
            mock_logger.debug.assert_called_once_with(f"OpenAIModel initialized with model: {self.model}")
    
    def test_model_attribute_set_correctly(self):
        """Test that model attribute is set correctly."""
        with patch('ai_utilities.openai_model.OpenAIClient'), \
             patch('ai_utilities.openai_model.RateLimiter') as mock_rate_limiter, \
             patch('ai_utilities.openai_model.ResponseProcessor'), \
             patch('ai_utilities.openai_model.TokenCounter'):
            
            mock_rate_limiter_instance = Mock()
            mock_rate_limiter.return_value = mock_rate_limiter_instance
            
            # Create model with custom model name
            custom_model = "gpt-4-turbo"
            model = OpenAIModel(self.api_key, custom_model, self.config, self.config_path)
            
            assert model.model == custom_model
