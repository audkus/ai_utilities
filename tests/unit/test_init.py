"""Tests for ai_utilities.__init__.py module."""

import importlib
import pytest
from unittest.mock import patch, MagicMock

import ai_utilities


class TestInitModule:
    """Test the main __init__.py module functionality."""

    def test_core_imports_available(self) -> None:
        """Test that core imports are available without lazy loading."""
        # These should be available immediately
        assert hasattr(ai_utilities, 'AiClient')
        assert hasattr(ai_utilities, 'AsyncAiClient')
        assert hasattr(ai_utilities, 'AiSettings')
        assert hasattr(ai_utilities, 'create_client')
        assert hasattr(ai_utilities, 'UploadedFile')
        assert hasattr(ai_utilities, 'JsonParseError')
        assert hasattr(ai_utilities, 'parse_json_from_text')
        assert hasattr(ai_utilities, 'AskResult')

    def test_version_available(self) -> None:
        """Test that version is available."""
        assert hasattr(ai_utilities, '__version__')
        assert isinstance(ai_utilities.__version__, str)
        assert len(ai_utilities.__version__) > 0

    @patch('ai_utilities.ssl_check.require_ssl_backend')
    def test_ssl_check_called_on_import(self, mock_require_ssl: MagicMock) -> None:
        """Test that SSL check is called during import."""
        # Get the module from sys.modules to ensure we have the right reference
        import sys
        ai_utilities_module = sys.modules['ai_utilities']
        
        # Re-import to trigger the SSL check
        import importlib
        importlib.reload(ai_utilities_module)
        mock_require_ssl.assert_called_once()

    def test_lazy_audio_imports(self) -> None:
        """Test lazy loading of audio processing functions."""
        # Test audio processing lazy imports
        audio_processor = ai_utilities.AudioProcessor
        assert audio_processor is not None
        
        load_audio = ai_utilities.load_audio_file
        assert load_audio is not None
        
        save_audio = ai_utilities.save_audio_file
        assert save_audio is not None
        
        validate_audio = ai_utilities.validate_audio_file
        assert validate_audio is not None
        
        get_audio_info = ai_utilities.get_audio_info
        assert get_audio_info is not None
        
        audio_format = ai_utilities.AudioFormat
        assert audio_format is not None

    def test_lazy_usage_tracker_imports(self) -> None:
        """Test lazy loading of usage tracking functions."""
        usage_tracker = ai_utilities.UsageTracker
        assert usage_tracker is not None
        
        create_usage_tracker = ai_utilities.create_usage_tracker
        assert create_usage_tracker is not None

    def test_lazy_openai_client_import(self) -> None:
        """Test lazy loading of OpenAI client."""
        openai_client = ai_utilities.OpenAIClient
        assert openai_client is not None

    def test_lazy_provider_imports(self) -> None:
        """Test lazy loading of provider classes."""
        base_provider = ai_utilities.BaseProvider
        assert base_provider is not None
        
        file_transfer_error = ai_utilities.FileTransferError
        assert file_transfer_error is not None
        
        openai_compatible = ai_utilities.OpenAICompatibleProvider
        assert openai_compatible is not None
        
        openai_provider = ai_utilities.OpenAIProvider
        assert openai_provider is not None
        
        provider_capabilities = ai_utilities.ProviderCapabilities
        assert provider_capabilities is not None
        
        provider_capability_error = ai_utilities.ProviderCapabilityError
        assert provider_capability_error is not None
        
        provider_configuration_error = ai_utilities.ProviderConfigurationError
        assert provider_configuration_error is not None
        
        create_provider = ai_utilities.create_provider
        assert create_provider is not None

    def test_lazy_rate_limit_imports(self) -> None:
        """Test lazy loading of rate limiting classes."""
        rate_limit_fetcher = ai_utilities.RateLimitFetcher
        assert rate_limit_fetcher is not None
        
        rate_limit_info = ai_utilities.RateLimitInfo
        assert rate_limit_info is not None

    def test_lazy_token_counter_import(self) -> None:
        """Test lazy loading of token counter."""
        token_counter = ai_utilities.TokenCounter
        assert token_counter is not None

    def test_lazy_usage_tracker_internals_imports(self) -> None:
        """Test lazy loading of usage tracker internal classes."""
        thread_safe = ai_utilities.ThreadSafeUsageTracker
        assert thread_safe is not None
        
        usage_scope = ai_utilities.UsageScope
        assert usage_scope is not None
        
        usage_stats = ai_utilities.UsageStats
        assert usage_stats is not None

    def test_lazy_submodule_imports(self) -> None:
        """Test lazy loading of submodules."""
        # Test a few key submodules
        client_module = ai_utilities.client
        assert client_module is not None
        
        config_models_module = ai_utilities.config_models
        assert config_models_module is not None
        
        file_models_module = ai_utilities.file_models
        assert file_models_module is not None

    def test_getattr_invalid_attribute(self) -> None:
        """Test that accessing invalid attributes raises AttributeError."""
        with pytest.raises(AttributeError) as exc_info:
            _ = ai_utilities.NonExistentAttribute
        
        assert "module 'ai_utilities' has no attribute 'NonExistentAttribute'" in str(exc_info.value)

    def test_getattr_caches_lazy_imports(self) -> None:
        """Test that lazy imports work correctly."""
        # Test that lazy import works
        client_module = ai_utilities.client
        assert client_module is not None
        
        # Test that second access returns the same object (cached)
        client_module2 = ai_utilities.client
        assert client_module is client_module2

    def test_all_exports(self) -> None:
        """Test that __all__ contains expected exports."""
        expected_exports = {
            'AiClient', 'AsyncAiClient', 'AiSettings', 'create_client', 'AskResult',
            'UploadedFile', 'JsonParseError', 'parse_json_from_text', 'UsageTracker',
            'create_usage_tracker', 'OpenAIClient', 'AudioProcessor', 'load_audio_file',
            'save_audio_file', 'validate_audio_file', 'get_audio_info',
            'ThreadSafeUsageTracker', 'UsageScope', 'UsageStats', 'RateLimitFetcher',
            'RateLimitInfo', 'TokenCounter', 'BaseProvider', 'OpenAIProvider',
            'OpenAICompatibleProvider', 'create_provider', 'ProviderCapabilities',
            'ProviderCapabilityError', 'ProviderConfigurationError', 'FileTransferError',
            'AudioFormat', 'AudioFile', 'TranscriptionRequest', 'TranscriptionResult',
            'AudioGenerationRequest', 'AudioGenerationResult'
        }
        
        actual_exports = set(ai_utilities.__all__)
        assert expected_exports.issubset(actual_exports)

    @patch('importlib.metadata.version')
    def test_version_fallback_on_import_error(self, mock_version: MagicMock) -> None:
        """Test version fallback when importlib.metadata raises ImportError."""
        mock_version.side_effect = ImportError("No module named 'importlib.metadata'")
        
        # Re-import to test version handling
        import importlib
        import sys
        
        # Remove ai_utilities from modules if present
        if 'ai_utilities' in sys.modules:
            del sys.modules['ai_utilities']
        
        # Re-import
        import ai_utilities as fresh_ai_utilities
        
        # Should fall back to hardcoded version
        assert fresh_ai_utilities.__version__ == "1.0.0b2"

    @patch('importlib.metadata.version')
    def test_version_from_metadata(self, mock_version: MagicMock) -> None:
        """Test version retrieval from importlib.metadata."""
        mock_version.return_value = "2.1.3"
        
        # Re-import to test version handling
        import importlib
        import sys
        
        # Remove ai_utilities from modules if present
        if 'ai_utilities' in sys.modules:
            del sys.modules['ai_utilities']
        
        # Re-import
        import ai_utilities as fresh_ai_utilities
        
        # Should use version from metadata
        assert fresh_ai_utilities.__version__ == "2.1.3"
        mock_version.assert_called_once_with("ai-utilities")
        
        # Clean up
        if 'ai_utilities' in sys.modules:
            del sys.modules['ai_utilities']

    def test_lazy_submodules_dict_complete(self) -> None:
        """Test that _LAZY_SUBMODULES contains expected mappings."""
        from ai_utilities import _LAZY_SUBMODULES
        
        # Check some key mappings
        assert 'client' in _LAZY_SUBMODULES
        assert _LAZY_SUBMODULES['client'] == 'ai_utilities.client'
        
        assert 'config_models' in _LAZY_SUBMODULES
        assert _LAZY_SUBMODULES['config_models'] == 'ai_utilities.config_models'
        
        assert 'providers' in _LAZY_SUBMODULES
        assert _LAZY_SUBMODULES['providers'] == 'ai_utilities.providers'

    def test_audio_lazy_import_specific_classes(self) -> None:
        """Test specific audio classes are lazy loaded."""
        audio_file = ai_utilities.AudioFile
        assert audio_file is not None
        
        transcription_request = ai_utilities.TranscriptionRequest
        assert transcription_request is not None
        
        transcription_result = ai_utilities.TranscriptionResult
        assert transcription_result is not None
        
        audio_generation_request = ai_utilities.AudioGenerationRequest
        assert audio_generation_request is not None
        
        audio_generation_result = ai_utilities.AudioGenerationResult
        assert audio_generation_result is not None
