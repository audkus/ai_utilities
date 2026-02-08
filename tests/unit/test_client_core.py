"""Comprehensive tests for client.py core functionality - Phase 7B."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest

from ai_utilities.client import _sanitize_namespace, _default_namespace, AiClient
from ai_utilities.config_models import AiSettings
from ai_utilities.models import AskResult
from ai_utilities.file_models import UploadedFile
from ai_utilities.providers.base_provider import BaseProvider
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


class TestSanitizeNamespace:
    """Test the _sanitize_namespace function."""
    
    def test_sanitize_namespace_basic(self):
        """Test basic namespace sanitization."""
        assert _sanitize_namespace("test") == "test"
        assert _sanitize_namespace("Test") == "test"
        assert _sanitize_namespace("  test  ") == "test"
    
    def test_sanitize_namespace_special_characters(self):
        """Test special character handling."""
        assert _sanitize_namespace("test@domain.com") == "test_domain.com"
        assert _sanitize_namespace("test#123") == "test_123"
        assert _sanitize_namespace("test/slash") == "test_slash"
        assert _sanitize_namespace("test\\backslash") == "test_backslash"
    
    def test_sanitize_namespace_consecutive_underscores(self):
        """Test consecutive underscore removal."""
        assert _sanitize_namespace("test__multiple___underscores") == "test_multiple_underscores"
        assert _sanitize_namespace("test___name") == "test_name"
    
    def test_sanitize_namespace_safe_characters(self):
        """Test that safe characters are preserved."""
        assert _sanitize_namespace("test.name-123") == "test.name-123"
        assert _sanitize_namespace("test_underscore") == "test_underscore"
        assert _sanitize_namespace("test-dash") == "test-dash"
        assert _sanitize_namespace("test.dots") == "test.dots"
    
    def test_sanitize_namespace_edge_cases(self):
        """Test edge cases."""
        # Empty string should return default
        assert _sanitize_namespace("") == "default"
        
        # Only special characters
        assert _sanitize_namespace("@@@") == "default"
        
        # Length limit (should be truncated if too long)
        long_name = "a" * 100
        result = _sanitize_namespace(long_name)
        assert len(result) <= 64  # Should be limited to 64 characters
    
    def test_sanitize_namespace_unicode(self):
        """Test unicode character handling."""
        assert _sanitize_namespace("testñame") == "testname"  # ñ transliterates to n
        assert _sanitize_namespace("тест") == "default"  # Non-latin chars should be replaced


class TestDefaultNamespace:
    """Test the _default_namespace function."""
    
    def test_default_namespace_basic(self):
        """Test basic default namespace generation."""
        with patch('ai_utilities.client.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/home/user/project")
            result = _default_namespace()
            # Current implementation uses hash for security
            assert result.startswith("proj_")
            assert len(result) == 17  # proj_ + 13 char hash (actual behavior)
    
    def test_default_namespace_with_custom_path(self):
        """Test default namespace with custom path."""
        test_path = Path("/custom/path/test")
        result = _default_namespace(test_path)
        # Current implementation uses hash for security
        assert result.startswith("proj_")
        assert len(result) == 17  # proj_ + 13 char hash (actual behavior)
        # Different paths should produce different hashes
        result2 = _default_namespace(Path("/different/path"))
        assert result != result2
    
    def test_default_namespace_sanitization(self):
        """Test that default namespace is properly sanitized."""
        with patch('ai_utilities.client.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/path with spaces/@weird#chars")
            result = _default_namespace()
            assert "@" not in result
            assert "#" not in result
            assert " " not in result


class TestAiClient:
    """Test the main AiClient class."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock AI settings."""
        return AiSettings(api_key="test_key", model="gpt-3.5-turbo")
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        provider = Mock(spec=BaseProvider)
        provider.ask.return_value = "Test response"
        provider.ask_many.return_value = ["Response 1", "Response 2"]
        return provider
    
    def test_client_initialization_with_settings(self, mock_settings):
        """Test client initialization with settings."""
        client = AiClient(mock_settings)
        assert client.settings.api_key == "test_key"
        assert client.settings.model == "gpt-3.5-turbo"
    
    def test_client_initialization_with_provider(self, mock_provider):
        """Test client initialization with custom provider."""
        client = AiClient(provider=mock_provider)
        assert client.provider is mock_provider
    
    def test_client_initialization_default_settings(self):
        """Test client initialization with default settings."""
        with patch('ai_utilities.client.Path') as mock_path, \
             patch('ai_utilities.client.AiSettings.from_dotenv') as mock_from_dotenv:
            # Mock that .env file exists
            mock_path.return_value.exists.return_value = True
            
            # Use real AiSettings object instead of mock
            from ai_utilities.config_models import AiSettings
            mock_settings = AiSettings(
                api_key="test_key", 
                model="gpt-3.5-turbo", 
                provider="openai",
                _env_file=None
            )
            mock_from_dotenv.return_value = mock_settings
            
            client = AiClient()
            
            mock_from_dotenv.assert_called_once_with(".env")
            assert client.settings.api_key == "test_key"
            assert client.settings.model == "gpt-3.5-turbo"
    
    def test_ask_method(self, mock_provider):
        """Test the ask method."""
        client = AiClient(provider=mock_provider)
        
        response = client.ask("What is 2+2?")
        
        # Current implementation passes settings + kwargs to provider
        mock_provider.ask.assert_called_once()
        call_args = mock_provider.ask.call_args
        assert call_args[0][0] == "What is 2+2?"
        assert call_args[1]["return_format"] == "text"
        # Settings parameters are also passed (model, temperature, etc.)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_method_with_json_format(self, mock_provider):
        """Test the ask method with JSON format."""
        client = AiClient(provider=mock_provider)
        
        client.ask("What is 2+2?", return_format="json")
        
        # Current implementation passes settings + kwargs to provider
        mock_provider.ask.assert_called_once()
        call_args = mock_provider.ask.call_args
        assert call_args[0][0] == "What is 2+2?"
        assert call_args[1]["return_format"] == "json"
    
    def test_ask_method_with_kwargs(self, mock_provider):
        """Test the ask method with additional kwargs."""
        client = AiClient(provider=mock_provider)
        
        client.ask("Test prompt", temperature=0.5, max_tokens=100)
        
        # Current implementation passes settings + kwargs to provider
        mock_provider.ask.assert_called_once()
        call_args = mock_provider.ask.call_args
        assert call_args[0][0] == "Test prompt"
        assert call_args[1]["return_format"] == "text"
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 100
    
    def test_ask_many_method(self, mock_provider):
        """Test the ask_many method."""
        client = AiClient(provider=mock_provider)
        
        prompts = ["Question 1", "Question 2"]
        results = client.ask_many(prompts)
        
        # Current implementation calls provider.ask for each prompt (not ask_many)
        assert mock_provider.ask.call_count == 2
        assert len(results) == 2
        # Results are AskResult objects, not strings
        # Since mock returns "Test response" for all calls, both results should have that
        assert results[0].response == "Test response"
        assert results[1].response == "Test response"
    
    def test_ask_many_method_with_json_format(self, mock_provider):
        """Test the ask_many method with JSON format."""
        client = AiClient(provider=mock_provider)
        
        prompts = ["Question 1", "Question 2"]
        results = client.ask_many(prompts, return_format="json")
        
        # Current implementation calls provider.ask for each prompt (not ask_many)
        assert mock_provider.ask.call_count == 2
        assert len(results) == 2
        # Check that return_format was passed correctly
        for call in mock_provider.ask.call_args_list:
            assert call[1]["return_format"] == "json"
    
    def test_ask_many_method_with_kwargs(self, mock_provider):
        """Test the ask_many method with additional kwargs."""
        client = AiClient(provider=mock_provider)
        
        prompts = ["Question 1", "Question 2"]
        results = client.ask_many(prompts, temperature=0.7, max_tokens=50)
        
        # Current implementation calls provider.ask for each prompt (not ask_many)
        assert mock_provider.ask.call_count == 2
        assert len(results) == 2
        # Check that kwargs were passed correctly
        for call in mock_provider.ask.call_args_list:
            assert call[1]["temperature"] == 0.7
            assert call[1]["max_tokens"] == 50
    
    def test_ask_method_error_handling(self, mock_provider):
        """Test error handling in ask method."""
        mock_provider.ask.side_effect = Exception("Provider error")
        
        client = AiClient(provider=mock_provider)
        
        with pytest.raises(Exception, match="Provider error"):
            client.ask("Test prompt")
    
    def test_ask_many_method_error_handling(self, mock_provider):
        """Test error handling in ask_many method."""
        mock_provider.ask.side_effect = Exception("Provider error")
        
        client = AiClient(provider=mock_provider)
        
        # Current implementation returns AskResult objects with errors, doesn't raise
        results = client.ask_many(["Question 1", "Question 2"])
        assert len(results) == 2
        assert results[0].error == "Provider error"
        assert results[1].error == "Provider error"
        assert results[0].response is None
        assert results[1].response is None
    
    def test_client_with_usage_tracking(self, mock_provider):
        """Test client with usage tracking enabled."""
        with patch('ai_utilities.client.create_usage_tracker') as mock_create_tracker:
            mock_tracker = Mock()
            mock_create_tracker.return_value = mock_tracker
            
            client = AiClient(
                provider=mock_provider, 
                track_usage=True
            )
            
            mock_create_tracker.assert_called_once()
            assert client.usage_tracker is mock_tracker
    
    def test_client_without_usage_tracking(self, mock_provider):
        """Test client with usage tracking disabled."""
        client = AiClient(
            provider=mock_provider, 
            track_usage=False
        )
        
        assert client.usage_tracker is None
    
    def test_client_with_cache(self, mock_provider):
        """Test client with caching enabled."""
        # Create a mock cache object
        mock_cache = Mock()
        
        # Pass cache object directly to client
        client = AiClient(provider=mock_provider, cache=mock_cache)
        
        # Client should use the provided cache object
        assert client.cache is mock_cache
    
    def test_client_without_cache(self, mock_provider):
        """Test client with caching disabled."""
        client = AiClient(
            provider=mock_provider, 
            cache=None
        )
        
        from ai_utilities.cache import NullCache
        assert isinstance(client.cache, NullCache)
    
    def test_client_file_operations_not_supported(self, mock_provider):
        """Test that file operations raise errors when files don't exist."""
        client = AiClient(provider=mock_provider)
        
        # Test with non-existent file - should raise ValueError for file existence check
        with pytest.raises(ValueError, match="File does not exist"):
            client.upload_file(Path("test.txt"))
    
    def test_client_image_generation_not_supported(self, mock_provider):
        """Test that image generation raises errors when not supported."""
        mock_provider.generate_image.side_effect = ProviderCapabilityError("image generation", "MockProvider")
        
        client = AiClient(provider=mock_provider)
        
        with pytest.raises(ProviderCapabilityError):
            client.generate_image("A test image")


class TestAiClientIntegration:
    """Integration tests for AiClient."""
    
    def test_client_end_to_end_workflow(self):
        """Test complete client workflow."""
        # Create a mock provider that simulates real responses
        mock_provider = Mock(spec=BaseProvider)
        mock_provider.ask.return_value = "The capital of France is Paris."
        mock_provider.ask_many.return_value = [
            "Response to question 1",
            "Response to question 2",
            "Response to question 3"
        ]
        
        # Create client
        settings = AiSettings(api_key="test_key", model="gpt-3.5-turbo")
        client = AiClient(settings=settings, provider=mock_provider)
        
        # Test single question
        response = client.ask("What is the capital of France?")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        
        # Test batch questions
        questions = [
            "What is 2+2?",
            "What is the capital of Spain?",
            "What is the largest planet?"
        ]
        responses = client.ask_many(questions)
        assert len(responses) == 3
        # Current implementation returns AskResult objects, not strings
        assert all(hasattr(r, 'response') for r in responses)
        assert all(r.response == "The capital of France is Paris." for r in responses)
        
        # Verify provider was called correctly (ask_many now calls ask multiple times)
        assert mock_provider.ask.call_count == 4  # 1 for single + 3 for batch
        assert mock_provider.ask_many.call_count == 0  # Not used anymore
    
    def test_client_with_different_return_formats(self):
        """Test client with different return formats."""
        mock_provider = Mock(spec=BaseProvider)
        mock_provider.ask.return_value = {"result": "json response"}
        
        client = AiClient(provider=mock_provider)
        
        # Test JSON format
        response = client.ask("Test question", return_format="json")
        assert response == {"result": "json response"}
        
        # Verify provider was called with correct format (current implementation passes settings too)
        mock_provider.ask.assert_called_once()
        call_args = mock_provider.ask.call_args
        assert call_args[0][0] == "Test question"
        assert call_args[1]["return_format"] == "json"
    
    def test_client_error_propagation(self):
        """Test that errors from provider are properly propagated."""
        mock_provider = Mock(spec=BaseProvider)
        mock_provider.ask.side_effect = ValueError("Invalid input")
        
        client = AiClient(provider=mock_provider)
        
        with pytest.raises(ValueError, match="Invalid input"):
            client.ask("Test question")
    
    @pytest.mark.requires_openai
    def test_client_parameter_validation(self):
        """Test client parameter validation."""
        # Current implementation validates API key at creation time for OpenAI
        from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
        
        settings = AiSettings(provider="openai", api_key=None)
        with pytest.raises(ProviderConfigurationError, match="API key is required|configuration error"):
            AiClient(settings=settings)
        
        # But local providers don't require API keys
        settings_local = AiSettings(provider="ollama", api_key=None, ollama_base_url="http://localhost:11434/v1", model="llama3")
        client = AiClient(settings=settings_local)
        assert client.settings.api_key is None
    
    def test_client_provider_fallback(self):
        """Test client provider fallback mechanism."""
        settings = AiSettings(api_key="test_key", model="gpt-3.5-turbo")
        
        # Create client without explicit provider
        client = AiClient(settings=settings)
        
        # Should create a provider (the exact type depends on configuration)
        assert client.provider is not None
        assert hasattr(client.provider, 'ask')  # Should have the provider interface
        
        # Verify settings were passed to client
        assert client.settings == settings


class TestAiClientAdvancedFeatures:
    """Test advanced AiClient features."""
    
    def test_client_with_progress_indicator(self):
        """Test client with progress indicator."""
        mock_provider = Mock(spec=BaseProvider)
        mock_provider.ask.return_value = "Test response"
        
        with patch('ai_utilities.client.ProgressIndicator') as mock_progress:
            # Create a proper mock with context manager support
            mock_progress_instance = Mock()
            mock_progress_instance.__enter__ = Mock(return_value=mock_progress_instance)
            mock_progress_instance.__exit__ = Mock(return_value=None)
            mock_progress.return_value = mock_progress_instance
            
            client = AiClient(
                provider=mock_provider, 
                show_progress=True
            )
            
            # Make a request to trigger progress indicator
            client.ask("Test question")
            
            # ProgressIndicator should be created when making a request
            mock_progress.assert_called_once_with(show=True)
    
    def test_client_with_custom_timeout(self):
        """Test client with custom timeout settings."""
        mock_provider = Mock(spec=BaseProvider)
        mock_provider.ask.return_value = "Test response"
        
        settings = AiSettings(api_key="test_key", model="gpt-3.5-turbo", timeout=30)
        client = AiClient(settings=settings, provider=mock_provider)
        
        assert client.settings.timeout == 30
    
    def test_client_with_retry_logic(self):
        """Test client retry logic."""
        mock_provider = Mock(spec=BaseProvider)
        # First call fails, second succeeds
        mock_provider.ask.side_effect = [Exception("Temporary error"), "Success"]
        
        client = AiClient(provider=mock_provider)
        
        # This would need retry logic implementation
        # For now, just test that the error is propagated
        with pytest.raises(Exception, match="Temporary error"):
            client.ask("Test question")
    
    def test_client_state_isolation(self):
        """Test that client instances are properly isolated."""
        mock_provider1 = Mock(spec=BaseProvider)
        mock_provider1.ask.return_value = "Response from client 1"
        
        mock_provider2 = Mock(spec=BaseProvider)
        mock_provider2.ask.return_value = "Response from client 2"
        
        client1 = AiClient(provider=mock_provider1)
        client2 = AiClient(provider=mock_provider2)
        
        response1 = client1.ask("Test")
        response2 = client2.ask("Test")
        
        assert response1 == "Response from client 1"
        assert response2 == "Response from client 2"
        assert client1.provider is not client2.provider
