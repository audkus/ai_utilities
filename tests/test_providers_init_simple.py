"""
Simple tests for providers/__init__.py to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch

# Test imports work correctly
def test_imports():
    """Test that all imports work correctly."""
    from ai_utilities.providers import (
        BaseProvider, 
        OpenAIProvider, 
        OpenAICompatibleProvider,
        create_provider,
        ProviderCapabilities,
        ProviderCapabilityError, 
        ProviderConfigurationError,
        FileTransferError,
        MissingOptionalDependencyError
    )
    
    # Verify all imports are successful
    assert BaseProvider is not None
    assert OpenAIProvider is not None
    assert OpenAICompatibleProvider is not None
    assert create_provider is not None
    assert ProviderCapabilities is not None
    assert ProviderCapabilityError is not None
    assert ProviderConfigurationError is not None
    assert FileTransferError is not None
    assert MissingOptionalDependencyError is not None


def test_all_exports():
    """Test __all__ contains expected exports."""
    from ai_utilities.providers import __all__
    
    expected = [
        "BaseProvider", 
        "OpenAIProvider", 
        "OpenAICompatibleProvider",
        "create_provider",
        "ProviderCapabilities",
        "ProviderCapabilityError", 
        "ProviderConfigurationError",
        "FileTransferError",
        "MissingOptionalDependencyError"
    ]
    
    assert __all__ == expected


def test_get_openai_provider_success():
    """Test successful OpenAI provider loading."""
    with patch('ai_utilities.providers.openai_provider.OpenAIProvider') as mock_openai:
        mock_provider_class = Mock()
        mock_openai.return_value = mock_provider_class
        
        from ai_utilities.providers import _get_openai_provider
        
        result = _get_openai_provider()
        
        # Should return the class, not an instance
        assert callable(result)
        mock_openai.assert_called_once()


def test_get_openai_provider_import_error():
    """Test OpenAI provider loading with import error."""
    with patch('ai_utilities.providers.openai_provider.OpenAIProvider', 
               side_effect=ImportError("No module named 'openai'")):
        
        from ai_utilities.providers import _get_openai_provider
        
        with pytest.raises(Exception) as exc_info:
            _get_openai_provider()
        
        assert "OpenAI provider requires extra 'openai'" in str(exc_info.value)
        assert "pip install ai-utilities[openai]" in str(exc_info.value)


def test_lazy_openai_provider_attribute_access():
    """Test LazyOpenAIProvider attribute access."""
    with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
        mock_provider_class = Mock()
        mock_attribute = Mock()
        mock_provider_class.some_attribute = mock_attribute
        mock_get_provider.return_value = mock_provider_class
        
        from ai_utilities.providers import OpenAIProvider
        
        result = OpenAIProvider.some_attribute
        
        assert result == mock_attribute
        mock_get_provider.assert_called_once()


def test_lazy_openai_provider_method_call():
    """Test LazyOpenAIProvider method call."""
    with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
        mock_provider_class = Mock()
        mock_method = Mock(return_value="method_result")
        mock_provider_class.some_method = mock_method
        mock_get_provider.return_value = mock_provider_class
        
        from ai_utilities.providers import OpenAIProvider
        
        result = OpenAIProvider.some_method("arg1", kwarg1="value1")
        
        assert result == "method_result"
        mock_method.assert_called_once_with("arg1", kwarg1="value1")


def test_lazy_openai_provider_class_attribute():
    """Test LazyOpenAIProvider class attribute access."""
    with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
        mock_provider_class = Mock()
        mock_class_attribute = "class_value"
        mock_provider_class.CLASS_ATTRIBUTE = mock_class_attribute
        mock_get_provider.return_value = mock_provider_class
        
        from ai_utilities.providers import OpenAIProvider
        
        result = OpenAIProvider.CLASS_ATTRIBUTE
        
        assert result == mock_class_attribute


def test_lazy_openai_provider_nonexistent_attribute():
    """Test LazyOpenAIProvider with non-existent attribute."""
    with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
        mock_provider_class = Mock()
        # Remove the attribute to trigger AttributeError
        del mock_provider_class.non_existent_attribute
        mock_get_provider.return_value = mock_provider_class
        
        from ai_utilities.providers import OpenAIProvider
        
        with pytest.raises(AttributeError):
            _ = OpenAIProvider.non_existent_attribute


def test_exception_hierarchy():
    """Test that provider exceptions work correctly."""
    # Import the exceptions to test them
    from ai_utilities.providers import (
        ProviderCapabilityError, ProviderConfigurationError, 
        FileTransferError, MissingOptionalDependencyError
    )
    
    # Test that exceptions can be raised and caught
    with pytest.raises(ProviderCapabilityError):
        raise ProviderCapabilityError("Test", "test_provider")
    
    with pytest.raises(ProviderConfigurationError):
        raise ProviderConfigurationError("Test", "test_provider")
    
    with pytest.raises(FileTransferError):
        raise FileTransferError("upload", "test_provider", Exception("test"))
    
    with pytest.raises(MissingOptionalDependencyError):
        raise MissingOptionalDependencyError("Test dependency")


def test_provider_capabilities():
    """Test ProviderCapabilities can be used."""
    from ai_utilities.providers import ProviderCapabilities
    
    capabilities = ProviderCapabilities()
    assert capabilities is not None


def test_base_provider_is_abstract():
    """Test that BaseProvider cannot be instantiated directly."""
    from ai_utilities.providers import BaseProvider
    
    with pytest.raises(TypeError):
        BaseProvider()


def test_openai_compatible_provider():
    """Test OpenAICompatibleProvider can be used."""
    from ai_utilities.providers import OpenAICompatibleProvider
    
    # Test that it exists and can be subclassed/instantiated with proper args
    # We can't test full instantiation without proper setup, but we can test it exists
    assert OpenAICompatibleProvider is not None


def test_create_provider_function():
    """Test create_provider function exists and can be called."""
    from ai_utilities.providers import create_provider
    
    # Test that the function exists
    assert callable(create_provider)
    
    # Test with mock to avoid actual provider creation
    with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create:
        mock_provider = Mock()
        mock_create.return_value = mock_provider
        
        # Pass proper settings dict with base_url
        settings = {"provider": "test", "base_url": "https://test.url"}
        result = create_provider(settings)
        
        assert result == mock_provider


def test_multiple_lazy_access():
    """Test multiple accesses to LazyOpenAIProvider."""
    with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
        mock_provider_class = Mock()
        mock_get_provider.return_value = mock_provider_class
        
        from ai_utilities.providers import OpenAIProvider
        
        # Access multiple times
        attr1 = OpenAIProvider.attr1
        attr2 = OpenAIProvider.attr2
        
        # Should call _get_openai_provider each time due to __getattr__
        assert mock_get_provider.call_count == 2


def test_lazy_provider_runtime_error():
    """Test LazyOpenAIProvider when _get_openai_provider raises RuntimeError."""
    with patch('ai_utilities.providers._get_openai_provider', 
               side_effect=RuntimeError("Provider error")):
        
        from ai_utilities.providers import OpenAIProvider
        
        # Should propagate the RuntimeError
        with pytest.raises(RuntimeError, match="Provider error"):
            _ = OpenAIProvider.some_attribute
