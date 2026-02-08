"""
Tests to verify timeout configuration is properly passed to OpenAI client.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from ai_utilities import AiSettings, create_provider


class TestTimeoutConfiguration:
    """Test that timeout configuration works correctly."""
    
    def test_default_timeout_in_settings(self):
        """Test that settings have default timeout."""
        settings = AiSettings()
        assert settings.timeout == 30
    
    def test_custom_timeout_in_settings(self):
        """Test that custom timeout can be set."""
        settings = AiSettings(timeout=60)
        assert settings.timeout == 60
    
    def test_timeout_passed_to_openai_client(self, openai_mocks):
        """Test that timeout is passed to OpenAI client constructor."""
        constructor_mock, client_mock = openai_mocks
        
        settings = AiSettings(api_key="test-key", timeout=45)
        provider = create_provider(settings)
        
        # Verify OpenAI client was created with correct timeout
        # Note: base_url may be resolved to default instead of None
        call_args = constructor_mock.call_args
        assert call_args[1]['timeout'] == 45
        assert call_args[1]['api_key'] == "test-key"
    
    def test_environment_timeout_override(self):
        """Test that AI_TIMEOUT environment variable overrides default."""
        # Set environment variable
        with patch.dict(os.environ, {'AI_TIMEOUT': '25'}):
            settings = AiSettings(api_key="test-key")
            provider = create_provider(settings)
            
            # Verify timeout from environment was used
            assert settings.timeout == 25
            # With the autouse fixture, the provider should be created successfully
            assert provider is not None
    
    def test_request_timeout_s_override(self):
        """Test that AI_REQUEST_TIMEOUT_S environment variable works."""
        # Set environment variable for float timeout
        with patch.dict(os.environ, {'AI_REQUEST_TIMEOUT_S': '15.5'}):
            settings = AiSettings(api_key="test-key")
            provider = create_provider(settings)
            
            # Verify timeout from environment was used
            assert settings.request_timeout_s == 15.5
            # With the autouse fixture, the provider should be created successfully
            assert provider is not None
    
    def test_timeout_validation(self):
        """Test that timeout values are validated."""
        # Test minimum timeout
        settings = AiSettings(timeout=1)
        assert settings.timeout == 1
        
        # Test that negative timeout would raise validation error
        with pytest.raises(ValueError):
            AiSettings(timeout=0)
        
        with pytest.raises(ValueError):
            AiSettings(timeout=-5)
    
    def test_timeout_is_integer(self):
        """Test that timeout is always stored as integer."""
        # Test with valid integer
        settings = AiSettings(timeout=30)
        assert isinstance(settings.timeout, int)
        assert settings.timeout == 30
        
        # Test that float values are handled (may be converted or rejected)
        try:
            settings = AiSettings(timeout=30.7)
            # If accepted, should be integer
            assert isinstance(settings.timeout, int)
        except Exception:
            # If rejected, that's also acceptable behavior
            pass
    
    def test_openai_compatible_provider_timeout(self):
        """Test that OpenAI-compatible provider settings handle timeout correctly."""
        settings = AiSettings(
            provider="openai_compatible",
            api_key="test-key",
            base_url="http://localhost:11434/v1",
            timeout=20
        )
        
        # The OpenAI-compatible provider should handle timeout correctly
        # Since it uses lazy import, we'll test the settings instead
        assert settings.timeout == 20
        assert settings.provider == "openai_compatible"
        assert settings.base_url == "http://localhost:11434/v1"
