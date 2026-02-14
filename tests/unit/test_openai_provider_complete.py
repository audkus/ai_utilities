"""
Comprehensive tests for OpenAIProvider to achieve 100% coverage.
"""

from __future__ import annotations
import sys
import importlib
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime
import json
from typing import Tuple
from types import ModuleType, SimpleNamespace
from ai_utilities.file_models import UploadedFile
from ai_utilities.providers.provider_exceptions import MissingOptionalDependencyError, FileTransferError


class TestOpenAIProviderComplete:
    """Comprehensive test suite for OpenAIProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_settings = Mock()
        self.mock_settings.api_key = "test-api-key"
        self.mock_settings.base_url = "https://api.openai.com/v1"
        self.mock_settings.timeout = 30
        self.mock_settings.model = "gpt-3.5-turbo"
        self.mock_settings.temperature = 0.7
        self.mock_settings.max_tokens = 1000
    
    def _create_provider_with_mock_client(self, mock_client, openai_provider_mod):
        """Helper to create provider with mock client for contract testing."""
        return openai_provider_mod.OpenAIProvider(self.mock_settings, client=mock_client)
    
    
    def test_initialization_success(self):
        """Test initialization raises MissingOptionalDependencyError when openai is missing."""
        from ai_utilities.providers.openai_provider import OpenAIProvider
        
        with pytest.raises(MissingOptionalDependencyError, match="OpenAI package is required"):
            OpenAIProvider(self.mock_settings)

    
    def test_initialization_with_custom_settings(self):
        """Test initialization raises MissingOptionalDependencyError when openai is missing."""
        from ai_utilities.providers.openai_provider import OpenAIProvider
        
        custom_settings = Mock()
        custom_settings.api_key = "custom-key"
        custom_settings.base_url = "https://custom.base.url"
        custom_settings.timeout = 60
        custom_settings.max_tokens = 2000
        
        with pytest.raises(MissingOptionalDependencyError, match="OpenAI package is required"):
            OpenAIProvider(custom_settings)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_text_response(self, mock_create_client, openai_provider_mod):
        """Test ask method with text response - contract level."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Test response"))]
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        # Contract: Provider can be constructed with settings and optional client
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        # Contract: ask() calls SDK with correct request shape
        result = provider.ask("Test prompt")
        
        # Verify API call shape (contract validation)
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Contract: Response parsing returns documented shape (string)
        assert result is not None
        assert isinstance(result, str)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_gpt4(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using GPT-4."""
        # Update settings to GPT-4
        self.mock_settings.model = "gpt-4"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"key": "value"}'))]
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("key") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_gpt35_turbo(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using GPT-3.5-turbo."""
        # Update settings to GPT-3.5-turbo
        self.mock_settings.model = "gpt-3.5-turbo"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"result": "success"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("result") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_claude(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using Claude."""
        # Update settings to Claude
        self.mock_settings.model = "claude-3-sonnet"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"data": "test"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="claude-3-sonnet",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("data") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_o1_models(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using O1 models."""
        # Update settings to O1
        self.mock_settings.model = "o1-preview"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"output": "result"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="o1-preview",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("output") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_o1_mini(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using O1-mini."""
        # Update settings to O1-mini
        self.mock_settings.model = "o1-mini"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"mini": "response"}'
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="o1-mini",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("mini") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_custom_model_with_json(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using custom model with 'json' in name."""
        # Update settings to custom model
        self.mock_settings.model = "custom-json-model"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"custom": "json"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="custom-json-model",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("custom") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_non_openai_provider(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response for non-OpenAI provider."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"provider": "custom"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        # Mock the provider_name property to return a non-OpenAI name
        with patch.object(type(provider), 'provider_name', new_callable=lambda: property(lambda self: "custom_provider")):
            result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call includes JSON response format (assumed support for non-OpenAI)
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("provider") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_unsupported_model(self, mock_create_client, openai_provider_mod):
        """Test ask method with JSON response using unsupported model."""
        # Update settings to unsupported model
        self.mock_settings.model = "text-davinci-003"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = 'Here is some text with {"json": "content"} embedded'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Verify API call does NOT include JSON response format
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="text-davinci-003",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Should extract JSON from text
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("json") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_invalid_json_in_native_mode(self, mock_create_client, openai_provider_mod):
        """Test ask method with invalid JSON in native JSON mode."""
        # Update settings to GPT-4 for JSON mode
        self.mock_settings.model = "gpt-4"
        
        # Mock OpenAI client response with invalid JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This is not valid JSON"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Should return wrapped response when JSON parsing fails
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("response") is not None  # Contract: wrapped response key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_json_response_no_json_found(self, mock_create_client, openai_provider_mod):
        """Test ask method with no JSON found in text."""
        # Update settings to unsupported model
        self.mock_settings.model = "text-davinci-003"
        
        # Mock OpenAI client response with no JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This is plain text with no JSON"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt", return_format="json")
        
        # Should return wrapped response when no JSON found
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("response") is not None  # Contract: wrapped response key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_with_custom_parameters(self, mock_create_client, openai_provider_mod):
        """Test ask method with custom parameters."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Custom response"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask(
            "Test prompt",
            model="gpt-4",
            temperature=0.5,
            max_tokens=500,
            return_format="text"
        )
        
        # Verify API call uses custom parameters
        mock_client.chat.completions.create.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            model="gpt-4",  # Custom model
            temperature=0.5,  # Custom temperature
            max_tokens=500  # Custom max tokens
        )
        
        # Contract: verify provider was called and returned a result (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_many_text_responses(self, mock_create_client, openai_provider_mod):
        """Test ask_many method with text responses."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = provider.ask_many(prompts)
        
        # Verify multiple API calls
        assert mock_client.chat.completions.create.call_count == 3
        assert isinstance(results, list)  # Contract: results is list type
        assert len(results) == 3  # Contract: expected number of responses
        assert all(isinstance(r, str) for r in results)  # Contract: all responses are strings
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_many_json_responses(self, mock_create_client, openai_provider_mod):
        """Test ask_many method with JSON responses."""
        # Update settings to GPT-4 for JSON mode
        self.mock_settings.model = "gpt-4"
        
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"result": "success"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        prompts = ["JSON Prompt 1", "JSON Prompt 2"]
        results = provider.ask_many(prompts, return_format="json")
        
        # Verify multiple API calls with JSON format
        assert mock_client.chat.completions.create.call_count == 2
        assert isinstance(results, list)  # Contract: results is list type
        assert len(results) == 2  # Contract: expected number of responses
        assert all(isinstance(r, dict) for r in results)  # Contract: all responses are dicts
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_ask_batch_method(self, mock_create_client, openai_provider_mod):
        """Test _ask_batch method directly."""
        # Mock OpenAI client response
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Batch response"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        prompts = ["Batch 1", "Batch 2"]
        results = provider._ask_batch(prompts)
        
        # Verify batch processing
        assert mock_client.chat.completions.create.call_count == 2
        assert isinstance(results, list)  # Contract: results is list type
        assert len(results) == 2  # Contract: expected number of responses
        assert all(isinstance(r, str) for r in results)  # Contract: all responses are strings
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_extract_json_valid_json(self, mock_create_client, openai_provider_mod):
        """Test _extract_json with valid JSON."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        text = 'Some text {"key": "value", "number": 123} more text'
        result = provider._extract_json(text)
        
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("key") is not None  # Contract: expected key present
        assert result.get("number") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_extract_json_multiple_json_objects(self, mock_create_client, openai_provider_mod):
        """Test _extract_json with multiple JSON objects."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        text = 'First {"first": 1} second {"second": 2} third'
        result = provider._extract_json(text)
        
        # Should extract the first valid JSON object
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("first") is not None  # Contract: expected key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_extract_json_invalid_json(self, mock_create_client, openai_provider_mod):
        """Test _extract_json with invalid JSON."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        text = 'Some text {invalid json} more text'
        result = provider._extract_json(text)
        
        # Should return wrapped response when JSON is invalid
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("response") is not None  # Contract: wrapped response key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_extract_json_no_json(self, mock_create_client, openai_provider_mod):
        """Test _extract_json with no JSON."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        text = 'Just plain text without any JSON'
        result = provider._extract_json(text)
        
        # Should return wrapped response when no JSON found
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("response") is not None  # Contract: wrapped response key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_extract_json_empty_string(self, mock_create_client, openai_provider_mod):
        """Test _extract_json with empty string."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        result = provider._extract_json("")
        
        # Should return wrapped response for empty string
        assert isinstance(result, dict)  # Contract: result is dict type
        assert result.get("response") is not None  # Contract: wrapped response key present
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_upload_file_success(self, mock_create_client, openai_provider_mod):
        """Test successful file upload."""
        # Mock file response
        mock_file_response = Mock()
        mock_file_response.id = "file-123"
        mock_file_response.filename = "test.txt"
        mock_file_response.bytes = 1024
        mock_file_response.purpose = "assistants"
        mock_file_response.created_at = "2024-01-01T00:00:00Z"
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.files.create.return_value = mock_file_response
        mock_create_client.return_value = mock_client
        
        # Create test file
        test_file = Path("/tmp/test.txt")
        
        # Create a real temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = Path(temp_file.name)
        
        try:
            # Mock the path methods to use our temp file
            with patch.object(Path, 'exists') as mock_exists, \
                 patch.object(Path, 'is_file') as mock_is_file:
                mock_exists.return_value = True
                mock_is_file.return_value = True
                
                provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
                result = provider.upload_file(temp_file_path)
            
            # Verify result
            assert isinstance(result, UploadedFile)
            assert isinstance(result.file_id, str)  # Contract: file_id is string type
            assert len(result.file_id) > 0  # Contract: non-empty file_id
            assert isinstance(result.filename, str)  # Contract: filename is string type
            assert len(result.filename) > 0  # Contract: non-empty filename
            assert isinstance(result.bytes, int)  # Contract: bytes is int type
            assert result.bytes > 0  # Contract: positive bytes
            assert isinstance(result.provider, str)  # Contract: provider is string type
            assert len(result.provider) > 0  # Contract: non-empty provider
            assert isinstance(result.purpose, str)  # Contract: purpose is string type
            assert len(result.purpose) > 0  # Contract: non-empty purpose
            
        finally:
            # Clean up temp file
            temp_file_path.unlink(missing_ok=True)
        assert isinstance(result.created_at, datetime)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_upload_file_with_custom_parameters(self, mock_create_client, openai_provider_mod):
        """Test file upload with custom parameters."""
        # Mock file response
        mock_file_response = Mock()
        mock_file_response.id = "file-456"
        mock_file_response.filename = "custom.pdf"
        mock_file_response.bytes = 2048
        mock_file_response.purpose = "fine-tune"
        mock_file_response.created_at = 1704067200  # Unix timestamp
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.files.create.return_value = mock_file_response
        mock_create_client.return_value = mock_client
        
        # Create a real temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as temp_file:
            temp_file.write("pdf content")
            temp_file_path = Path(temp_file.name)
        
        try:
            # Mock the path methods to use our temp file
            with patch.object(Path, 'exists') as mock_exists, \
                 patch.object(Path, 'is_file') as mock_is_file:
                mock_exists.return_value = True
                mock_is_file.return_value = True
                
                provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
                result = provider.upload_file(
                    temp_file_path,
                    purpose="fine-tune",
                    filename="custom.pdf",
                    mime_type="application/pdf"
                )
            
            # Verify result
            assert isinstance(result, UploadedFile)
            assert isinstance(result.file_id, str)  # Contract: file_id is string type
            assert len(result.file_id) > 0  # Contract: non-empty file_id
            assert isinstance(result.filename, str)  # Contract: filename is string type
            assert len(result.filename) > 0  # Contract: non-empty filename
            assert isinstance(result.bytes, int)  # Contract: bytes is int type
            assert result.bytes > 0  # Contract: positive bytes
            assert isinstance(result.provider, str)  # Contract: provider is string type
            assert len(result.provider) > 0  # Contract: non-empty provider
            assert isinstance(result.purpose, str)  # Contract: purpose is string type
            assert len(result.purpose) > 0  # Contract: non-empty purpose
            
            # Verify upload was called
            mock_client.files.create.assert_called_once()
            
        finally:
            # Clean up temp file
            temp_file_path.unlink(missing_ok=True)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_upload_file_not_a_file(self, mock_create_client, openai_provider_mod):
        """Test file upload when path is not a file."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        test_file = Path("/tmp/directory")
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=False):
                provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
                
                with pytest.raises(ValueError, match="Path is not a file"):
                    provider.upload_file(test_file)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_upload_file_api_error(self, mock_create_client, openai_provider_mod):
        """Test file upload when API call fails."""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_client.files.create.side_effect = Exception("API Error")
        mock_create_client.return_value = mock_client
        
        test_file = Path("/tmp/test.txt")
        
        with patch('builtins.open', mock_open(read_data=b"test content")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
                    
                    with pytest.raises(FileTransferError) as exc_info:
                        provider.upload_file(test_file)
                    
                    assert "upload" in str(exc_info.value)
                    assert "openai" in str(exc_info.value)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_download_file_success(self, mock_create_client, openai_provider_mod):
        """Test successful file download."""
        # Mock file content response
        mock_content_response = Mock()
        mock_content_response.content = b"file content"
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.files.content.return_value = mock_content_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.download_file("file-123")
        
        # Verify download call
        mock_client.files.content.assert_called_once_with("file-123")
        
        # Verify result
        assert isinstance(result, bytes)  # Contract: result is bytes type
        assert len(result) > 0  # Contract: non-empty file content
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_download_file_empty_id(self, mock_create_client, openai_provider_mod):
        """Test file download with empty file ID."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        with pytest.raises(ValueError, match="file_id cannot be empty"):
            provider.download_file("")
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_download_file_api_error(self, mock_create_client, openai_provider_mod):
        """Test file download when API call fails."""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_client.files.content.side_effect = Exception("Download Error")
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        with pytest.raises(FileTransferError) as exc_info:
            provider.download_file("file-123")
        
        assert "download" in str(exc_info.value)
        assert "openai" in str(exc_info.value)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_generate_image_success(self, mock_create_client, openai_provider_mod):
        """Test successful image generation."""
        # Mock image response
        mock_image_response = Mock()
        mock_image = Mock()
        mock_image.url = "https://example.com/image1.png"
        mock_image_response.data = [mock_image]
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.images.generate.return_value = mock_image_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.generate_image("A beautiful sunset")
        
        # Verify generation call
        mock_client.images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt="A beautiful sunset",
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Verify result
        assert isinstance(result, list)  # Contract: result is list type
        assert len(result) > 0  # Contract: non-empty image list
        assert all(isinstance(url, str) for url in result)  # Contract: all URLs are strings
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_generate_image_multiple_images(self, mock_create_client, openai_provider_mod):
        """Test image generation with multiple images."""
        # Mock image response
        mock_image_response = Mock()
        mock_images = [Mock(url=f"https://example.com/image{i}.png") for i in range(3)]
        mock_image_response.data = mock_images
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.images.generate.return_value = mock_image_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.generate_image("Three cats", n=3)
        
        # Verify generation call
        mock_client.images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt="Three cats",
            size="1024x1024",
            quality="standard",
            n=3
        )
        
        # Verify result
        assert isinstance(result, list)  # Contract: result is list type
        assert len(result) == 3  # Contract: expected number of images
        assert all(isinstance(url, str) for url in result)  # Contract: all URLs are strings
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_generate_image_custom_parameters(self, mock_create_client, openai_provider_mod):
        """Test image generation with custom parameters."""
        # Mock image response
        mock_image_response = Mock()
        mock_image = Mock()
        mock_image.url = "https://example.com/custom.png"
        mock_image_response.data = [mock_image]
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.images.generate.return_value = mock_image_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.generate_image(
            "HD image",
            size="1792x1024",
            quality="hd",
            n=2
        )
        
        # Verify generation call with custom parameters
        mock_client.images.generate.assert_called_once_with(
            model="dall-e-3",
            prompt="HD image",
            size="1792x1024",
            quality="hd",
            n=2
        )
        
        assert isinstance(result, list)  # Contract: result is list type
        assert len(result) > 0  # Contract: non-empty image list
        assert all(isinstance(url, str) for url in result)  # Contract: all URLs are strings
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_generate_image_empty_prompt(self, mock_create_client, openai_provider_mod):
        """Test image generation with empty prompt."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            provider.generate_image("")
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_generate_image_invalid_n(self, mock_create_client, openai_provider_mod):
        """Test image generation with invalid n parameter."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        # Test n < 1
        with pytest.raises(ValueError, match="n must be between 1 and 10"):
            provider.generate_image("test", n=0)
        
        # Test n > 10
        with pytest.raises(ValueError, match="n must be between 1 and 10"):
            provider.generate_image("test", n=11)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_generate_image_api_error(self, mock_create_client, openai_provider_mod):
        """Test image generation when API call fails."""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_client.images.generate.side_effect = Exception("Generation Error")
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        with pytest.raises(FileTransferError) as exc_info:
            provider.generate_image("test image")
        
        assert "image generation" in str(exc_info.value)
        assert "openai" in str(exc_info.value)
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_provider_name_property(self, mock_create_client, openai_provider_mod):
        """Test provider_name property."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        
        # Test that provider_name is accessible
        assert hasattr(provider, 'provider_name')
    
    @patch('ai_utilities.providers.openai_provider._create_openai_sdk_client')
    def test_empty_response_content(self, mock_create_client, openai_provider_mod):
        """Test handling of empty response content."""
        # Mock OpenAI client response with None content
        mock_client = Mock()
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        provider = self._create_provider_with_mock_client(mock_client, openai_provider_mod)
        result = provider.ask("Test prompt")
        
        # Should handle None content gracefully
        # Contract: verify error handling returns content (passthrough)
        assert result is not None
        assert isinstance(result, str)  # Verify return type contract
