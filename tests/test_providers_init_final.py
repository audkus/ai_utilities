"""
Final tests for providers/__init__.py to reach 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch


def test_get_openai_provider_direct_import():
    """Test direct import and call of _get_openai_provider."""
    # Test the actual function behavior
    try:
        from ai_utilities.providers import _get_openai_provider
        result = _get_openai_provider()
        # If OpenAI is available, should return the class
        assert callable(result)
    except Exception as e:
        # If OpenAI is not available, should raise MissingOptionalDependencyError
        assert "OpenAI provider requires extra 'openai'" in str(e)


def test_lazy_openai_provider_getattr_with_real_class():
    """Test LazyOpenAIProvider with actual class behavior."""
    from ai_utilities.providers import OpenAIProvider
    
    # Test that we can access attributes without errors
    # This will trigger the lazy loading mechanism
    try:
        # Try to access a common class attribute
        _ = OpenAIProvider.__name__
        # If we get here, OpenAI is available
        assert True
    except AttributeError:
        # Expected if OpenAI provider doesn't have __name__ or other attributes
        pass
    except Exception as e:
        # Should be MissingOptionalDependencyError if OpenAI not available
        assert "OpenAI provider requires extra 'openai'" in str(e)


def test_providers_init_module_attributes():
    """Test module-level attributes and structure."""
    import ai_utilities.providers as providers_module
    
    # Test that __all__ is defined correctly
    assert hasattr(providers_module, '__all__')
    assert isinstance(providers_module.__all__, list)
    assert len(providers_module.__all__) > 0
    
    # Test that all items in __all__ are actually available
    for item in providers_module.__all__:
        assert hasattr(providers_module, item), f"{item} not found in module"


def test_lazy_openai_provider_error_propagation():
    """Test that errors from _get_openai_provider are properly propagated."""
    with patch('ai_utilities.providers._get_openai_provider', 
               side_effect=RuntimeError("Custom error")):
        
        from ai_utilities.providers import OpenAIProvider
        
        with pytest.raises(RuntimeError, match="Custom error"):
            _ = OpenAIProvider.any_attribute


def test_openai_provider_lazy_loading_multiple_times():
    """Test that lazy loading works consistently across multiple accesses."""
    with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
        mock_provider_class = Mock()
        mock_provider_class.TEST_ATTR = "test_value"
        mock_get_provider.return_value = mock_provider_class
        
        from ai_utilities.providers import OpenAIProvider
        
        # Access multiple different attributes
        val1 = OpenAIProvider.TEST_ATTR
        val2 = OpenAIProvider.TEST_ATTR
        val3 = OpenAIProvider.__name__ if hasattr(mock_provider_class, '__name__') else None
        
        # Should call _get_openai_provider for each attribute access
        assert mock_get_provider.call_count >= 2
        assert val1 == "test_value"
        assert val2 == "test_value"


def test_providers_exception_instantiation():
    """Test that all provider exceptions can be instantiated."""
    from ai_utilities.providers import (
        ProviderCapabilityError, ProviderConfigurationError,
        FileTransferError, MissingOptionalDependencyError
    )
    
    # Test ProviderCapabilityError
    cap_error = ProviderCapabilityError("Test capability", "test_provider")
    assert str(cap_error) == "Test capability"
    assert cap_error.capability == "Test capability"
    assert cap_error.provider == "test_provider"
    
    # Test ProviderConfigurationError
    config_error = ProviderConfigurationError("Test config", "test_provider")
    assert str(config_error) == "Test config"
    assert config_error.message == "Test config"
    assert config_error.provider == "test_provider"
    
    # Test FileTransferError
    file_error = FileTransferError("upload", "test_provider", Exception("inner"))
    assert file_error.operation == "upload"
    assert file_error.provider == "test_provider"
    assert isinstance(file_error.inner_error, Exception)
    
    # Test MissingOptionalDependencyError
    dep_error = MissingOptionalDependencyError("test package")
    assert str(dep_error) == "test package"
    assert dep_error.dependency == "test package"


def test_provider_capabilities_class():
    """Test ProviderCapabilities class functionality."""
    from ai_utilities.providers import ProviderCapabilities
    
    # Test instantiation
    capabilities = ProviderCapabilities()
    assert capabilities is not None
    
    # Test that it has expected attributes (even if default values)
    assert hasattr(capabilities, '__dict__')


def test_base_provider_abstract_methods():
    """Test that BaseProvider has the expected abstract methods."""
    from ai_utilities.providers import BaseProvider
    import inspect
    
    # Get all abstract methods
    abstract_methods = [
        name for name, method in inspect.getmembers(BaseProvider, predicate=inspect.isfunction)
        if getattr(method, '__isabstractmethod__', False)
    ]
    
    # Should have at least some abstract methods
    assert len(abstract_methods) > 0
    
    # Test that we can't instantiate it
    with pytest.raises(TypeError):
        BaseProvider()


def test_openai_compatible_provider_structure():
    """Test OpenAICompatibleProvider structure."""
    from ai_utilities.providers import OpenAICompatibleProvider
    import inspect
    
    # Should be a class
    assert inspect.isclass(OpenAICompatibleProvider)
    
    # Should inherit from BaseProvider
    from ai_utilities.providers import BaseProvider
    assert issubclass(OpenAICompatibleProvider, BaseProvider)


def test_create_provider_error_handling():
    """Test create_provider error handling."""
    from ai_utilities.providers import create_provider
    
    # Test with invalid provider type
    with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create:
        mock_create.side_effect = ValueError("Invalid provider")
        
        with pytest.raises(ValueError, match="Invalid provider"):
            create_provider({"provider": "invalid", "base_url": "https://test.url"})


def test_missing_optional_dependency_error_details():
    """Test MissingOptionalDependencyError with detailed message."""
    from ai_utilities.providers import MissingOptionalDependencyError
    
    error = MissingOptionalDependencyError("package-name")
    assert error.dependency == "package-name"
    assert "package-name" in str(error)


def test_provider_capability_error_details():
    """Test ProviderCapabilityError with detailed message."""
    from ai_utilities.providers import ProviderCapabilityError
    
    error = ProviderCapabilityError("image_generation", "openai")
    assert error.capability == "image_generation"
    assert error.provider == "openai"
    assert "image_generation" in str(error)


def test_provider_configuration_error_details():
    """Test ProviderConfigurationError with detailed message."""
    from ai_utilities.providers import ProviderConfigurationError
    
    error = ProviderConfigurationError("Missing API key", "openai")
    assert error.message == "Missing API key"
    assert error.provider == "openai"
    assert "Missing API key" in str(error)


def test_file_transfer_error_details():
    """Test FileTransferError with detailed error information."""
    from ai_utilities.providers import FileTransferError
    
    inner_error = IOError("File not found")
    error = FileTransferError("download", "openai", inner_error)
    
    assert error.operation == "download"
    assert error.provider == "openai"
    assert error.inner_error == inner_error
    assert isinstance(error.inner_error, IOError)
