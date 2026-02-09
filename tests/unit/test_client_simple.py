"""Simple focused tests for client.py core functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ai_utilities.client import _sanitize_namespace, _default_namespace, AiClient
from ai_utilities.config_models import AiSettings
from ai_utilities.providers.base_provider import BaseProvider


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
    
    def test_sanitize_namespace_consecutive_underscores(self):
        """Test consecutive underscore removal."""
        assert _sanitize_namespace("test__multiple___underscores") == "test_multiple_underscores"
    
    def test_sanitize_namespace_safe_characters(self):
        """Test that safe characters are preserved."""
        assert _sanitize_namespace("test.name-123") == "test.name-123"
        assert _sanitize_namespace("test_underscore") == "test_underscore"
    
    def test_sanitize_namespace_empty(self):
        """Test empty string handling."""
        assert _sanitize_namespace("") == "default"
        assert _sanitize_namespace("@@@") == "default"
    
    def test_sanitize_namespace_length_limit(self):
        """Test length limit."""
        long_name = "a" * 100
        result = _sanitize_namespace(long_name)
        assert len(result) <= 50  # Should be limited to 50 characters


class TestDefaultNamespace:
    """Test the _default_namespace function."""
    
    def test_default_namespace_format(self):
        """Test default namespace format."""
        result = _default_namespace()
        assert result.startswith("proj_")
        assert len(result) == 4 + 1 + 12  # "proj_" + "_" + 12 char hash
        assert result.replace("_", "").replace("proj", "").isalnum()


class TestAiClientBasic:
    """Test basic AiClient functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock AI settings."""
        return AiSettings(api_key="test_key", model="gpt-3.5-turbo")
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        provider = Mock(spec=BaseProvider)
        provider.ask.return_value = "Test response"
        return provider
    
    def test_client_initialization_with_settings(self, mock_settings):
        """Test client initialization with settings."""
        client = AiClient(mock_settings)
        assert client.settings.api_key == "test_key"
        assert client.settings.model == "gpt-3.5-turbo"
        assert client.provider is not None
    
    def test_client_initialization_with_provider(self, mock_provider):
        """Test client initialization with custom provider."""
        client = AiClient(provider=mock_provider)
        assert client.provider is mock_provider
    
    def test_client_initialization_default(self):
        """Test client initialization with default settings."""
        with patch('ai_utilities.client.AiSettings') as mock_settings_class, \
             patch('ai_utilities.client.Path') as mock_path:
            # Mock Path.exists() to return False so it doesn't try to load from .env
            mock_path.return_value.exists.return_value = False
            
            mock_settings = Mock()
            mock_settings.api_key = "default_key"
            mock_settings.model = "gpt-3.5-turbo"
            mock_settings.provider = "openai"
            mock_settings.base_url = "https://api.openai.com/v1"
            mock_settings.temperature = 0.7
            mock_settings.max_tokens = 1000
            mock_settings.timeout = 30
            # Configure Mock to return proper values for attribute access
            mock_settings.configure_mock(**{
                'api_key': "default_key",
                'model': "gpt-3.5-turbo", 
                'provider': "openai",
                'base_url': "https://api.openai.com/v1",
                'temperature': 0.7,
                'max_tokens': 1000,
                'timeout': 30
            })
            # Configure model_copy to return a copy with proper string values
            mock_copy = Mock()
            mock_copy.configure_mock(**{
                'api_key': "default_key",
                'model': "gpt-3.5-turbo", 
                'provider': "openai",
                'base_url': "https://api.openai.com/v1",
                'temperature': 0.7,
                'max_tokens': 1000,
                'timeout': 30
            })
            mock_settings.model_copy.return_value = mock_copy
            mock_settings_class.return_value = mock_settings
            
            client = AiClient()
            
            mock_settings_class.assert_called_once()
            assert client.settings is mock_settings
    
    def test_ask_single_prompt(self, mock_provider):
        """Test asking a single prompt."""
        client = AiClient(provider=mock_provider)
        
        response = client.ask("What is 2+2?")
        
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        # Provider should be called (we can't easily verify the exact call due to caching)
    
    def test_ask_with_json_format(self, mock_provider):
        """Test asking with JSON format."""
        mock_provider.ask.return_value = {"result": "json response"}
        
        client = AiClient(provider=mock_provider)
        
        response = client.ask("Test question", return_format="json")
        
        assert response == {"result": "json response"}
    
    def test_ask_multiple_prompts(self, mock_provider):
        """Test asking multiple prompts."""
        mock_provider.ask_many.return_value = ["Response", "Response"]
        
        client = AiClient(provider=mock_provider)
        
        prompts = ["Question 1", "Question 2"]
        responses = client.ask(prompts)
        
        assert responses == ["Response", "Response"]
        assert len(responses) == 2
    
    def test_ask_with_kwargs(self, mock_provider):
        """Test asking with additional parameters."""
        client = AiClient(provider=mock_provider)
        
        client.ask("Test prompt", temperature=0.5, max_tokens=100)
        
        # Should not raise an exception
        assert True
    
    def test_client_with_usage_tracking(self, mock_provider):
        """Test client with usage tracking enabled."""
        with patch('ai_utilities.client.create_usage_tracker') as mock_create_tracker:
            mock_tracker = Mock()
            mock_create_tracker.return_value = mock_tracker
            
            client = AiClient(provider=mock_provider, track_usage=True)
            
            mock_create_tracker.assert_called_once()
    
    def test_client_without_usage_tracking(self, mock_provider):
        """Test client with usage tracking disabled."""
        client = AiClient(provider=mock_provider, track_usage=False)
        
        assert client.usage_tracker is None
    
    def test_client_with_cache(self, mock_provider):
        """Test client with cache."""
        from ai_utilities.cache import NullCache
        
        client = AiClient(provider=mock_provider, cache=None)
        
        # Should have some kind of cache
        assert hasattr(client, 'cache')
    
    def test_client_error_handling(self, mock_provider):
        """Test error handling."""
        mock_provider.ask.side_effect = Exception("Provider error")
        
        client = AiClient(provider=mock_provider)
        
        with pytest.raises(Exception, match="Provider error"):
            client.ask("Test prompt")


class TestAiClientCaching:
    """Test AiClient caching functionality."""
    
    def test_cache_key_building(self):
        """Test cache key building."""
        settings = AiSettings(api_key="test", model="gpt-3.5-turbo")
        client = AiClient(settings=settings)
        
        # Test that cache key can be built
        key = client._build_cache_key(
            "ask",
            prompt="test prompt",
            request_params={"temperature": 0.5},
            return_format="text"
        )
        
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_should_use_cache(self):
        """Test cache usage decision."""
        settings = AiSettings(api_key="test", model="gpt-3.5-turbo", cache_enabled=True)
        client = AiClient(settings=settings)
        
        # Should use cache for normal requests
        assert client._should_use_cache({"temperature": 0.5}) is True
        
        # Should not use cache when disabled
        settings.cache_enabled = False
        assert client._should_use_cache({"temperature": 0.5}) is False
    
    def test_should_not_use_cache_high_temperature(self):
        """Test that high temperature requests are not cached."""
        settings = AiSettings(
            api_key="test", 
            model="gpt-3.5-turbo", 
            cache_enabled=True,
            cache_max_temperature=0.8
        )
        client = AiClient(settings=settings)
        
        # Should not use cache for high temperature
        assert client._should_use_cache({"temperature": 0.9}) is False
        
        # Should use cache for normal temperature
        assert client._should_use_cache({"temperature": 0.7}) is True


class TestAiClientAdvanced:
    """Test advanced AiClient features."""
    
    def test_check_for_updates(self):
        """Test update checking."""
        settings = AiSettings(api_key="test", model="gpt-3.5-turbo")
        client = AiClient(settings=settings)
        
        # Should return some kind of result
        result = client.check_for_updates()
        assert isinstance(result, dict)
    
    def test_client_state_isolation(self):
        """Test that client instances are isolated."""
        settings1 = AiSettings(api_key="key1", model="gpt-3.5-turbo")
        settings2 = AiSettings(api_key="key2", model="gpt-4")
        
        client1 = AiClient(settings=settings1)
        client2 = AiClient(settings=settings2)
        
        assert client1.settings.api_key != client2.settings.api_key
        assert client1.settings.model != client2.settings.model
        assert client1.provider is not client2.provider
