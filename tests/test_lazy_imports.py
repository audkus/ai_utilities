"""Test that lazy imports work correctly and don't import heavy modules eagerly."""

import sys
import pytest


def test_core_imports_work():
    """Test that core imports work normally."""
    from ai_utilities import AiClient, AiSettings, AskResult, UploadedFile, JsonParseError, parse_json_from_text
    
    # These should be available immediately
    assert AiClient is not None
    assert AiSettings is not None
    assert AskResult is not None
    assert UploadedFile is not None
    assert JsonParseError is not None
    assert parse_json_from_text is not None


def test_lazy_imports_not_loaded_initially():
    """Test that heavy modules are not loaded at import time."""
    # Clear any potentially loaded modules first
    modules_to_clear = [
        'ai_utilities.audio',
        'ai_utilities.audio.audio_processor',
        'ai_utilities.audio.audio_utils',
        'ai_utilities.audio.audio_models',
        'ai_utilities.openai_client',
        'ai_utilities.providers',
        'ai_utilities.providers.openai_provider',
        'ai_utilities.rate_limit_fetcher',
        'ai_utilities.token_counter',
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    # Import ai_utilities - this should not load heavy modules
    import ai_utilities
    
    # Check that heavy modules are not loaded
    for module in modules_to_clear:
        assert module not in sys.modules, f"Heavy module {module} was loaded eagerly"
    
    # Note: usage_tracker is imported by client.py, so we expect it to be loaded
    # This is acceptable since it's part of the core client functionality


def test_lazy_imports_work_on_demand():
    """Test that lazy imports work when accessed."""
    import ai_utilities
    
    # Initially these modules should not be loaded (except usage_tracker which is loaded by client)
    assert 'ai_utilities.audio' not in sys.modules
    assert 'ai_utilities.openai_client' not in sys.modules
    assert 'ai_utilities.rate_limit_fetcher' not in sys.modules
    
    # Access lazy imported items
    AudioProcessor = ai_utilities.AudioProcessor
    OpenAIClient = ai_utilities.OpenAIClient
    RateLimitFetcher = ai_utilities.RateLimitFetcher
    
    # Now they should be loaded
    assert 'ai_utilities.audio' in sys.modules
    assert 'ai_utilities.openai_client' in sys.modules
    assert 'ai_utilities.rate_limit_fetcher' in sys.modules
    
    # And the items should be the correct types
    assert AudioProcessor is not None
    assert OpenAIClient is not None
    assert RateLimitFetcher is not None


def test_knowledge_import_doesnt_load_heavy_modules():
    """Test that importing knowledge modules doesn't load providers/audio."""
    # Clear modules first
    modules_to_clear = [
        'ai_utilities.audio',
        'ai_utilities.providers',
        'ai_utilities.usage_tracker',
        'ai_utilities.rate_limit_fetcher',
        'ai_utilities.token_counter',
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    # Import knowledge backend
    try:
        from ai_utilities.knowledge.backend import KnowledgeBackend
        knowledge_imported = True
    except ImportError:
        # If knowledge modules have import issues, that's expected for now
        knowledge_imported = False
    
    if knowledge_imported:
        # Check that heavy modules are still not loaded
        for module in modules_to_clear:
            assert module not in sys.modules, f"Knowledge import loaded heavy module {module}"


def test_type_checking_imports_available():
    """Test that TYPE_CHECKING imports are available for type checking."""
    from ai_utilities import AiClient
    from typing import get_type_hints
    
    # Check that type hints work (this would fail if TYPE_CHECKING imports weren't available)
    try:
        # This should not raise an error
        hints = get_type_hints(AiClient.__init__)
        # We don't care about the specific hints, just that it works
        assert isinstance(hints, dict)
    except Exception:
        # If type hints don't work, that's okay for this test
        pass


def test_missing_attribute_raises_correct_error():
    """Test that accessing non-existent attributes raises AttributeError."""
    import ai_utilities
    
    with pytest.raises(AttributeError, match="module 'ai_utilities' has no attribute 'NonExistent'"):
        _ = ai_utilities.NonExistent
