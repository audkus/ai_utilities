"""
test_single_responsibility_refactoring.py

Tests for Single Responsibility Principle refactoring components.
"""

import os
import sys
from configparser import ConfigParser
from unittest.mock import Mock, patch
from types import ModuleType
import importlib

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.exceptions import RateLimitExceededError
from ai_utilities.openai_model import OpenAIModel
from ai_utilities.response_processor import ResponseProcessor
from ai_utilities.token_counter import TokenCounter


@pytest.fixture
def openai_client_mod(openai_mocks) -> ModuleType:
    """Import ai_utilities.openai_client AFTER openai_mocks has patched constructors."""
    sys.modules.pop("ai_utilities.openai_client", None)
    return importlib.import_module("ai_utilities.openai_client")


class TestOpenAIClient:
    """Test OpenAIClient single responsibility for API communication."""
    
    def test_initialization(self, openai_mocks, openai_client_mod):
        """Test OpenAIClient initialization."""
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        assert client.client is not None
        assert client.api_key == "test-key"
    
    def test_initialization_with_custom_base_url(self, openai_mocks, openai_client_mod):
        """Test OpenAIClient initialization with custom base URL."""
        client = openai_client_mod.OpenAIClient(
            api_key="test-key",
            base_url="https://custom.openai.com/v1",
            timeout=60
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://custom.openai.com/v1"
        assert client.timeout == 60
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_create_chat_completion(self, mock_openai, openai_client_mod):
        """Test chat completion creation."""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        response = client.create_chat_completion(
            model="test-model-1",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5
        )
        
        # Verify the API was called correctly
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-model-1",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5
        )
        assert response == mock_response
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_get_models(self, mock_openai, openai_client_mod):
        """Test model listing."""
        mock_models = Mock()
        mock_client = Mock()
        mock_client.models.list.return_value = mock_models
        mock_openai.return_value = mock_client
        
        client = openai_client_mod.OpenAIClient(api_key="test-key")
        models = client.get_models()
        
        mock_client.models.list.assert_called_once()
        assert models == mock_models


class TestResponseProcessor:
    """Test ResponseProcessor single responsibility for response processing."""
    
    def test_extract_json_valid(self):
        """Test JSON extraction from valid response."""
        response = "Here's some text {\"key\": \"value\"} more text"
        result = ResponseProcessor.extract_json(response)
        assert result == "{\"key\": \"value\"}"
    
    def test_extract_json_invalid(self):
        """Test JSON extraction from invalid response."""
        response = "No JSON here, just text"
        result = ResponseProcessor.extract_json(response)
        assert result == response
    
    def test_extract_json_partial(self):
        """Test JSON extraction from partial response."""
        response = "Start {\"key\": \"value\"} end"
        result = ResponseProcessor.extract_json(response)
        assert result == "{\"key\": \"value\"}"
    
    def test_is_valid_json_true(self):
        """Test valid JSON detection."""
        valid_json = "{\"key\": \"value\"}"
        assert ResponseProcessor.is_valid_json(valid_json) is True
    
    def test_is_valid_json_false(self):
        """Test invalid JSON detection."""
        invalid_json = "{key: value}"  # Missing quotes
        assert ResponseProcessor.is_valid_json(invalid_json) is False
    
    def test_clean_text(self):
        """Test text cleaning."""
        messy_text = "  Multiple   spaces   and\n\twhitespace  "
        result = ResponseProcessor.clean_text(messy_text)
        assert result == "Multiple spaces and whitespace"
    
    def test_format_response_text(self):
        """Test response formatting for text."""
        response = "  Clean this text  "
        result = ResponseProcessor.format_response(response, "text")
        assert result == "Clean this text"
    
    def test_format_response_json(self):
        """Test response formatting for JSON."""
        response = "Text {\"json\": \"content\"} more text"
        result = ResponseProcessor.format_response(response, "json")
        assert result == "{\"json\": \"content\"}"
    
    def test_extract_code_blocks(self):
        """Test code block extraction."""
        response = """Some text
```python
def hello():
    print("Hello")
```
More text
```javascript
console.log("Hello");
```
"""
        
        # Extract all code blocks
        all_blocks = ResponseProcessor.extract_code_blocks(response)
        assert len(all_blocks) == 2
        assert "def hello():" in all_blocks[0]
        assert "console.log" in all_blocks[1]
        
        # Extract specific language
        python_blocks = ResponseProcessor.extract_code_blocks(response, "python")
        assert len(python_blocks) == 1
        assert "def hello():" in python_blocks[0]


class TestTokenCounter:
    """Test TokenCounter single responsibility for token counting."""
    
    def test_count_tokens_word_method(self):
        """Test token counting by word method."""
        text = "This is a test sentence with eight words"
        result = TokenCounter.count_tokens(text, "word")
        # Should be approximately words / 0.75 (word-to-token ratio)
        assert result == int(len(text.split()) / 0.75)
    
    def test_count_tokens_char_method(self):
        """Test token counting by character method."""
        text = "This is a test"
        result = TokenCounter.count_tokens(text, "char")
        # Should be approximately chars / 4.0 (char-to-token ratio)
        assert result == int(len(text) / 4.0)
    
    def test_count_tokens_combined_method(self):
        """Test token counting by combined method."""
        text = "This is a test sentence"
        result = TokenCounter.count_tokens(text, "combined")
        # Should be average of word and char methods
        word_count = int(len(text.split()) / 0.75)
        char_count = int(len(text) / 4.0)
        expected = int((word_count + char_count) / 2)
        assert result == expected
    
    def test_count_empty_text(self):
        """Test token counting with empty text."""
        result = TokenCounter.count_tokens("", "word")
        assert result == 0
    
    def test_count_invalid_method(self):
        """Test token counting with invalid method."""
        with pytest.raises(ValueError):
            TokenCounter.count_tokens("test", "invalid")
    
    def test_count_message_tokens(self):
        """Test token counting for messages."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]
        
        result = TokenCounter.count_message_tokens(messages, "word")
        
        # Expected breakdown:
        # Message 1: content=6, role=1, overhead=4 = 11
        # Message 2: content=5, role=1, overhead=4 = 10  
        # Message 3: content=6, role=1, overhead=4 = 11
        # Total: 32
        assert result == 32
    
    def test_estimate_response_tokens(self):
        """Test response token estimation."""
        prompt_tokens = 100
        result = TokenCounter.estimate_response_tokens(prompt_tokens, 1.5)
        assert result == 150
    
    def test_count_tokens_for_model(self):
        """Test model-specific token counting."""
        text = "This is a longer test sentence with more words to demonstrate model differences"
        
        # Different models should have different adjustments
        gpt4_tokens = TokenCounter.count_tokens_for_model(text, "test-model-1")
        gpt35_tokens = TokenCounter.count_tokens_for_model(text, "test-model-2")
        
        # GPT-3.5-turbo should have higher token count (less efficient)
        assert gpt35_tokens > gpt4_tokens
    
    def test_count_tokens_unknown_model(self):
        """Test token counting for unknown model."""
        text = "This is a test"
        result = TokenCounter.count_tokens_for_model(text, "unknown-model")
        # Should use default adjustment (1.0)
        assert result == TokenCounter.count_tokens(text, "combined")


class TestOpenAIModelRefactoring:
    """Test OpenAIModel composition and single responsibilities."""
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_composition_initialization(self, mock_rate_limiter, mock_token_counter, 
                                      mock_response_processor, mock_openai_client):
        """Test that OpenAIModel properly composes its components."""
        # Setup mocks
        mock_client_instance = Mock()
        mock_openai_client.return_value = mock_client_instance
        mock_processor_instance = Mock()
        mock_response_processor.return_value = mock_processor_instance
        mock_counter_instance = Mock()
        mock_token_counter.return_value = mock_counter_instance
        mock_limiter_instance = Mock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Create config
        config = ConfigParser()
        config.add_section('test-model-1')
        config.set('test-model-1', 'requests_per_minute', '5000')
        config.set('test-model-1', 'tokens_per_minute', '450000')
        config.set('test-model-1', 'tokens_per_day', '1350000')
        
        # Initialize OpenAIModel
        model = OpenAIModel(api_key="test-key", model="test-model-1", config=config, config_path="test")
        
        # Verify components were initialized
        mock_openai_client.assert_called_once_with(api_key="test-key")
        mock_response_processor.assert_called_once()
        mock_token_counter.assert_called_once()
        mock_rate_limiter.assert_called_once()
        
        # Verify components are stored
        assert model.api_client == mock_client_instance
        assert model.response_processor == mock_processor_instance
        assert model.token_counter == mock_counter_instance
        assert model.rate_limiter == mock_limiter_instance
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_ask_ai_composition_flow(self, mock_rate_limiter, mock_token_counter,
                                   mock_response_processor, mock_openai_client):
        """Test that ask_ai properly uses composed components."""
        # Setup mocks
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "  Test response  "
        mock_client_instance.create_chat_completion.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        mock_processor_instance = Mock()
        mock_processor_instance.format_response.return_value = "Test response"
        mock_response_processor.return_value = mock_processor_instance
        
        mock_counter_instance = Mock()
        mock_counter_instance.count_tokens_for_model.return_value = 10
        mock_token_counter.return_value = mock_counter_instance
        
        mock_limiter_instance = Mock()
        mock_limiter_instance.can_proceed.return_value = True
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Create model
        config = ConfigParser()
        config.add_section('test-model-1')
        config.set('test-model-1', 'requests_per_minute', '5000')
        config.set('test-model-1', 'tokens_per_minute', '450000')
        config.set('test-model-1', 'tokens_per_day', '1350000')
        
        model = OpenAIModel(api_key="test-key", model="test-model-1", config=config, config_path="test")
        
        # Test ask_ai
        result = model.ask_ai("Hello", return_format="text")
        
        # Verify component usage
        mock_counter_instance.count_tokens_for_model.assert_called_once_with("Hello", "test-model-1")
        mock_limiter_instance.can_proceed.assert_called_once_with(10)
        mock_client_instance.create_chat_completion.assert_called_once()
        mock_processor_instance.format_response.assert_called_once_with("Test response", "text")
        
        assert result == "Test response"
    
    @patch('ai_utilities.openai_model.OpenAIClient')
    @patch('ai_utilities.openai_model.ResponseProcessor')
    @patch('ai_utilities.openai_model.TokenCounter')
    @patch('ai_utilities.openai_model.RateLimiter')
    def test_ask_ai_rate_limit_exceeded(self, mock_rate_limiter, mock_token_counter,
                                       mock_response_processor, mock_openai_client):
        """Test rate limit handling in ask_ai."""
        # Setup mocks
        mock_openai_client.return_value = Mock()
        mock_response_processor.return_value = Mock()
        mock_token_counter.return_value = Mock()
        
        mock_limiter_instance = Mock()
        mock_limiter_instance.can_proceed.return_value = False
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Create model
        config = ConfigParser()
        config.add_section('test-model-1')
        config.set('test-model-1', 'requests_per_minute', '5000')
        config.set('test-model-1', 'tokens_per_minute', '450000')
        config.set('test-model-1', 'tokens_per_day', '1350000')
        
        model = OpenAIModel(api_key="test-key", model="test-model-1", config=config, config_path="test")
        
        # Test rate limit exception
        with pytest.raises(RateLimitExceededError):
            model.ask_ai("Hello")
    
    def test_clean_response_deprecation_warning(self, caplog):
        """Test that clean_response shows deprecation warning."""
        caplog.set_level('WARNING')  # Ensure we capture warnings
        
        with patch('ai_utilities.openai_model.ResponseProcessor') as mock_processor:
            mock_processor.extract_json.return_value = '{"test": "data"}'
            
            # Call as static method and expect deprecation warning
            with pytest.warns(DeprecationWarning, match="OpenAIModel.clean_response.*is deprecated"):
                result = OpenAIModel.clean_response('{"test": "data"}')
            
            assert "deprecated" in caplog.text.lower()
            assert result == '{"test": "data"}'


class TestComponentIntegration:
    """Test integration between refactored components."""
    
    @patch('ai_utilities.openai_client.OpenAI')
    def test_end_to_end_workflow(self, mock_openai, openai_mocks, openai_client_mod):
        """Test end-to-end workflow with all components."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "  {\"answer\": \"test\"}  "
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create components
        api_client = openai_client_mod.OpenAIClient(api_key="test-key")
        processor = ResponseProcessor()
        counter = TokenCounter()
        
        # Simulate workflow
        prompt = "What is 2+2?"
        tokens = counter.count_tokens_for_model(prompt, "test-model-1")
        
        # API call
        response = api_client.create_chat_completion(
            model="test-model-1",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Process response
        raw_text = response.choices[0].message.content.strip()
        formatted_response = processor.format_response(raw_text, "json")
        
        # Verify workflow
        assert tokens > 0
        assert formatted_response == "{\"answer\": \"test\"}"
        mock_client.chat.completions.create.assert_called_once()
