"""Test minimal install functionality."""

from unittest.mock import patch, MagicMock


def test_minimal_import_without_openai():
    """Test that importing ai_utilities works without openai installed."""
    # Mock openai import to raise ImportError
    with patch.dict('sys.modules', {'openai': MagicMock()}):
        # Make the openai module raise ImportError when imported
        sys_modules_backup = {}
        try:
            # Backup original modules
            import sys
            original_import = __builtins__['__import__']
            
            # Mock import to raise ImportError for openai
            def mock_import(name, *args, **kwargs):
                if name.startswith('openai'):
                    raise ImportError("No module named 'openai'")
                return original_import(name, *args, **kwargs)
            
            __builtins__['__import__'] = mock_import
            
            # Test that basic import works
            import ai_utilities
            from ai_utilities import AiClient, AiSettings, AskResult
            
            # Test that creating settings works
            settings = AiSettings(provider="openai")  # Default provider
            assert settings.provider == "openai"
            
            # Test that we can import and create basic objects
            # But creating actual providers will fail without OpenAI SDK
            assert AiSettings is not None
            assert AiClient is not None
            assert AskResult is not None
            
        finally:
            # Restore original import
            __builtins__['__import__'] = original_import
