"""Tests for public API surface and stability."""

import pytest
import ai_utilities


def test_stable_public_api():
    """Test that the stable public API exports are available.
    
    This test defines the intentionally stable public API for ai_utilities v1.0.
    Items not listed here are considered internal and may change without notice.
    """
    # Core stable API - these are guaranteed to remain stable in v1.x
    stable_exports = {
        # Core client classes
        'AiClient',
        'AsyncAiClient', 
        'AiSettings',
        'create_client',
        'AskResult',
        
        # File handling
        'UploadedFile',
        'JsonParseError', 
        'parse_json_from_text',
        
        # Audio processing (stable but may be moved to submodule in future)
        'AudioProcessor',
        'load_audio_file',
        'save_audio_file',
        'validate_audio_file',
        'get_audio_info',
    }
    
    # All current exports (for backwards compatibility check)
    current_exports = set(ai_utilities.__all__)
    
    # Verify all stable exports are available
    for export in stable_exports:
        assert export in current_exports, f"Stable export {export} is missing"
        assert hasattr(ai_utilities, export), f"Stable export {export} not importable"
    
    # Verify stable exports can be imported
    for export in stable_exports:
        if export in ['create_client', 'parse_json_from_text', 'load_audio_file', 'save_audio_file', 'validate_audio_file', 'get_audio_info']:
            # These are functions
            assert callable(getattr(ai_utilities, export)), f"Export {export} should be callable"
        else:
            # These are classes
            assert isinstance(getattr(ai_utilities, export), type), f"Export {export} should be a class"


def test_additional_exports_exist_for_compatibility():
    """Test that additional exports exist for backwards compatibility.
    
    These exports are available for backwards compatibility but are not
    considered part of the stable API and may change in future versions.
    """
    # These are currently exported but considered implementation details
    compatibility_exports = {
        # Usage tracking (may be moved to ai_utilities.usage in future)
        'UsageTracker',
        'ThreadSafeUsageTracker', 
        'UsageScope',
        'UsageStats',
        'create_usage_tracker',
        
        # Rate limiting (may be moved to ai_utilities.rate_limit in future)
        'RateLimitFetcher',
        'RateLimitInfo',
        
        # Token counting (may be moved to ai_utilities.tokens in future)
        'TokenCounter',
        
        # Providers (implementation details - should use ai_utilities.providers)
        'BaseProvider',
        'OpenAIProvider',
        'OpenAICompatibleProvider', 
        'create_provider',
        'ProviderCapabilities',
        'ProviderCapabilityError',
        'ProviderConfigurationError',
        'FileTransferError',
        
        # Audio models (may be moved to ai_utilities.audio.models in future)
        'AudioFormat',
        'AudioFile',
        'TranscriptionRequest',
        'TranscriptionResult',
        'AudioGenerationRequest',
        'AudioGenerationResult',
    }
    
    current_exports = set(ai_utilities.__all__)
    
    # Verify compatibility exports are still available (for now)
    for export in compatibility_exports:
        assert export in current_exports, f"Compatibility export {export} is missing"
        assert hasattr(ai_utilities, export), f"Compatibility export {export} not importable"


def test_api_imports_work_correctly():
    """Test that the most common import patterns work correctly."""
    # Core imports should work
    from ai_utilities import AiClient, AiSettings, AskResult
    from ai_utilities import AsyncAiClient, create_client
    from ai_utilities import UploadedFile, JsonParseError, parse_json_from_text
    
    # Audio imports should work  
    from ai_utilities import AudioProcessor, load_audio_file
    
    # Verify they're the right types
    assert isinstance(AiClient, type)
    assert isinstance(AiSettings, type)
    assert callable(create_client)
    assert callable(parse_json_from_text)
    assert isinstance(AudioProcessor, type)


def test_no_internal_leaks():
    """Test that internal modules don't leak into public API."""
    # These should NOT be in the public API
    internal_names = {
        'os', 'sys', 'json', 'pathlib', 'datetime', 'uuid', 'time',
        'typing', 'dataclasses', 'enum', 'abc', 'collections',
        'BaseProvider',  # Should be in providers submodule
    }
    
    current_exports = set(ai_utilities.__all__)
    
    # Check that internal names don't leak (with some exceptions for legitimate exports)
    for name in internal_names:
        if name in ['BaseProvider']:  # This one is intentionally exported for now
            continue
        assert name not in current_exports, f"Internal name {name} leaked to public API"
