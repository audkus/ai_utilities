"""Comprehensive Phase 7 tests for client.py core functionality."""

import pytest
from unittest.mock import patch, MagicMock

def test_sanitize_namespace_comprehensive():
    """Test the _sanitize_namespace function comprehensively."""
    from ai_utilities.client import _sanitize_namespace
    
    # Test basic functionality
    assert _sanitize_namespace("test") == "test"
    assert _sanitize_namespace("Test") == "test"
    assert _sanitize_namespace("  test  ") == "test"
    
    # Test special characters (dots preserved)
    assert _sanitize_namespace("test@domain.com") == "test_domain.com"
    assert _sanitize_namespace("test#123") == "test_123"
    assert _sanitize_namespace("test/slash") == "test_slash"
    
    # Test consecutive underscores
    assert _sanitize_namespace("test__multiple___underscores") == "test_multiple_underscores"
    
    # Test safe characters
    assert _sanitize_namespace("test.name-123") == "test.name-123"
    assert _sanitize_namespace("test_underscore") == "test_underscore"
    
    # Test empty string
    assert _sanitize_namespace("") == "default"
    
    # Test length limit
    long_namespace = "a" * 100
    result = _sanitize_namespace(long_namespace)
    assert len(result) <= 50
    assert result == "a" * 50

def test_default_namespace():
    """Test the _default_namespace function."""
    from ai_utilities.client import _default_namespace
    
    result = _default_namespace()
    assert isinstance(result, str)
    assert len(result) > 0
    # Should be based on current working directory
    assert "proj_" in result or result == "default"

def test_client_initialization_minimal():
    """Test minimal client initialization."""
    from ai_utilities import AiClient, AiSettings
    
    settings = AiSettings(api_key="test-key", _env_file=None)
    client = AiClient(settings=settings)
    
    assert client.settings.api_key == "test-key"
    assert hasattr(client, 'provider')

def test_client_with_explicit_provider():
    """Test client with explicit provider."""
    from ai_utilities import AiClient, AiSettings
    from ai_utilities.providers.base_provider import BaseProvider
    
    mock_provider = MagicMock(spec=BaseProvider)
    settings = AiSettings(api_key="test-key", _env_file=None)
    
    with patch('ai_utilities.providers.create_provider', return_value=mock_provider):
        client = AiClient(settings=settings)
        assert client.provider is mock_provider

def test_client_cache_configuration():
    """Test client cache configuration."""
    from ai_utilities import AiClient, AiSettings
    from ai_utilities.cache import NullCache
    
    settings = AiSettings(api_key="test-key", _env_file=None)
    custom_cache = NullCache()
    
    with patch('ai_utilities.providers.create_provider'):
        client = AiClient(settings=settings, cache=custom_cache)
        assert client.cache is custom_cache
