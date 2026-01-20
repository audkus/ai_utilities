"""
Tests to improve code coverage for easy wins.
These target specific lines that are currently uncovered.
"""

import pytest
from unittest.mock import patch, MagicMock
from ai_utilities.file_models import UploadedFile
from ai_utilities.providers.provider_capabilities import ProviderCapabilities
from ai_utilities.exceptions import (
    AIUsageDisabledError, 
    InvalidPromptError, 
    MemoryUsageExceededError, 
    RateLimitExceededError, 
    LoggingError
)


class TestCoverageImprovements:
    """Tests to improve coverage for high-impact, low-effort areas."""
    
    def test_uploaded_file_str_and_repr(self):
        """Test string representations of UploadedFile."""
        uploaded_file = UploadedFile(
            file_id="test_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants"
        )
        
        # Test __str__ method (line 40-43)
        str_result = str(uploaded_file)
        assert "UploadedFile(id=test_123, filename=test.txt, provider=openai)" in str_result
        
        # Test __repr__ method (line 47-49)
        repr_result = repr(uploaded_file)
        assert "UploadedFile(file_id='test_123', filename='test.txt'" in repr_result
        assert "bytes=1024" in repr_result
        assert "provider='openai'" in repr_result
        assert "purpose=assistants" in repr_result
    
    def test_uploaded_file_datetime_serializer_none(self):
        """Test datetime serializer with None value (line 36)."""
        uploaded_file = UploadedFile(
            file_id="test_123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants"
        )
        
        # Test the serialize_created_at method with None
        result = uploaded_file.serialize_created_at(None)
        assert result is None
    
    def test_provider_capabilities_openai_compatible(self):
        """Test openai_compatible class method (line 55)."""
        # Import the actual class and call the method
        from ai_utilities.providers.provider_capabilities import ProviderCapabilities
        
        # Call the method that's missing coverage
        result = ProviderCapabilities.openai_compatible()
        
        # Verify the result has the expected capabilities
        assert result.supports_text is True
        assert result.supports_json_mode is True
        assert result.supports_streaming is False
        assert result.supports_tools is False
        assert result.supports_images is False
        assert result.supports_files_upload is False
        assert result.supports_files_download is False
        assert result.supports_temperature is True
        assert result.supports_max_tokens is True
        assert result.supports_top_p is False
        assert result.supports_frequency_penalty is False
        assert result.supports_presence_penalty is False
    
    def test_provider_capabilities_openai(self):
        """Test openai class method (line 36)."""
        # Import the actual class and call the method
        from ai_utilities.providers.provider_capabilities import ProviderCapabilities
        
        # Call the method that's missing coverage
        result = ProviderCapabilities.openai()
        
        # Verify the result has the expected capabilities for OpenAI
        assert result.supports_text is True
        assert result.supports_json_mode is True
        assert result.supports_streaming is True
        assert result.supports_tools is True
        assert result.supports_images is True
        assert result.supports_files_upload is True
        assert result.supports_files_download is True
        assert result.supports_temperature is True
        assert result.supports_max_tokens is True
        assert result.supports_top_p is True
        assert result.supports_frequency_penalty is True
        assert result.supports_presence_penalty is True

    def test_exception_constructors_with_logging(self):
        """Test exception constructors that perform logging (lines 38-67)."""
        # Test AIUsageDisabledError (lines 38-39)
        with patch('logging.error') as mock_log:
            error = AIUsageDisabledError("Custom message")
            assert str(error) == "Custom message"
            mock_log.assert_called_once_with("AIUsageDisabledError: Custom message")
        
        # Test InvalidPromptError (lines 45-46)
        with patch('logging.error') as mock_log:
            error = InvalidPromptError("Invalid prompt")
            assert str(error) == "Invalid prompt"
            mock_log.assert_called_once_with("InvalidPromptError: Invalid prompt")
        
        # Test MemoryUsageExceededError (lines 52-53)
        with patch('logging.error') as mock_log:
            error = MemoryUsageExceededError("Memory exceeded")
            assert str(error) == "Memory exceeded"
            mock_log.assert_called_once_with("MemoryUsageExceededError: Memory exceeded")
        
        # Test RateLimitExceededError (lines 59-60)
        with patch('logging.error') as mock_log:
            error = RateLimitExceededError("Rate limit exceeded")
            assert str(error) == "Rate limit exceeded"
            mock_log.assert_called_once_with("RateLimitExceededError: Rate limit exceeded")
        
        # Test LoggingError (lines 66-67)
        with patch('logging.error') as mock_log:
            error = LoggingError("Logging failed")
            assert str(error) == "Logging failed"
            mock_log.assert_called_once_with("LoggingError: Logging failed")

    def test_openai_client_methods(self, openai_mocks, OpenAIClient):
        """Test OpenAI client methods to improve coverage."""
        constructor_mock, client_mock = openai_mocks
        
        # Test get_models method (lines 96-97)
        mock_models = MagicMock()
        client_mock.models.list.return_value = mock_models
        
        client = OpenAIClient(api_key="test-key")
        result = client.get_models()
        assert result is mock_models
        client_mock.models.list.assert_called_once()


class TestVersionImportFallback:
    """Test version import fallback mechanism."""
    
    @patch('importlib.metadata.version', side_effect=ImportError("No module named 'version'"))
    def test_version_fallback_on_import_error(self, mock_version):
        """Test version fallback when importlib.metadata fails (lines 138-140)."""
        # Re-import to trigger the fallback path
        import sys
        
        # Remove the module if it exists to force re-import
        if 'ai_utilities' in sys.modules:
            del sys.modules['ai_utilities']
        
        # Re-import the module with the patched version function
        with patch('importlib.metadata.version', side_effect=ImportError):
            from ai_utilities import __version__
            
            # Should fallback to the hardcoded version
            assert __version__ == "1.0.0b2"
    
    @patch('importlib.metadata.version')
    def test_version_normal_import(self, mock_version):
        """Test normal version import path."""
        mock_version.return_value = "2.0.0"
        
        # Re-import to test normal path
        import sys
        if 'ai_utilities' in sys.modules:
            del sys.modules['ai_utilities']
        
        with patch('importlib.metadata.version', mock_version):
            from ai_utilities import __version__
            assert __version__ == "2.0.0"
