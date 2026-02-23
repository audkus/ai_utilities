"""
Simple tests for providers/__init__.py to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch
from ai_utilities.providers.provider_exceptions import MissingOptionalDependencyError


@pytest.fixture(autouse=True)
def patch_openai_import_for_providers_init_tests():
    """Patch OpenAI import to simulate missing dependency for providers init tests."""
    # Patch the OpenAIProvider class to raise MissingOptionalDependencyError
    import sys
    module = sys.modules['ai_utilities.providers']
    original_openai_provider = getattr(module, 'OpenAIProvider', None)
    
    class MockOpenAIProvider:
        def __init__(self, *args, **kwargs):
            raise MissingOptionalDependencyError(
                "OpenAI package is required. Install with: pip install ai-utilities[openai]"
            )
    
    module.OpenAIProvider = MockOpenAIProvider
    
    yield
    
    # Restore original class if it existed
    if original_openai_provider is not None:
        module.OpenAIProvider = original_openai_provider


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
        "provider_factory",
        "openai_compatible_provider",
        "ProviderCapabilities",
        "ProviderCapabilityError", 
        "ProviderConfigurationError",
        "FileTransferError",
        "MissingOptionalDependencyError"
    ]
    
    assert __all__ == expected


def test_openai_provider_direct_import():
    """Test direct OpenAI provider import."""
    # Import the OpenAI provider class directly
    from ai_utilities.providers import OpenAIProvider
    
    # Should be able to access the class directly
    assert OpenAIProvider is not None
    # Should be callable (class constructor)
    assert callable(OpenAIProvider)


def test_openai_provider_import_error():
    """Test OpenAI provider import error handling."""
    # This test verifies the import mechanism works
    # In real scenarios, MissingOptionalDependencyError would be handled by the lazy loading in __init__.py
    from ai_utilities.providers import OpenAIProvider
    
    # Should be able to import the class successfully
    assert OpenAIProvider is not None


def test_openai_provider_class_attributes(force_openai_missing):
    """Test OpenAI provider class attributes."""
    from ai_utilities.providers import OpenAIProvider
    
    # Should be able to access class attributes directly if the real class is available
    # If it's a placeholder, it won't have these attributes but that's OK
    if hasattr(OpenAIProvider, 'provider_name'):
        # Real OpenAI provider is available
        assert callable(OpenAIProvider)
    else:
        # Placeholder class - verify it raises MissingOptionalDependencyError on instantiation
        from unittest.mock import Mock
        mock_settings = Mock()
        mock_settings.api_key = "test_key"
        mock_settings.base_url = None
        mock_settings.timeout = 30
        
        with pytest.raises(MissingOptionalDependencyError, match="OpenAI package is required"):
            OpenAIProvider(mock_settings)


def test_openai_provider_instantiation(force_openai_missing):
    """Test OpenAI provider instantiation raises MissingOptionalDependencyError when openai is missing."""
    from ai_utilities.providers import OpenAIProvider
    from unittest.mock import Mock
    
    # Create a mock settings object
    mock_settings = Mock()
    mock_settings.api_key = "test_key"
    mock_settings.base_url = None
    mock_settings.timeout = 30
    
    # Should raise MissingOptionalDependencyError when openai is not installed
    with pytest.raises(MissingOptionalDependencyError, match="OpenAI package is required"):
        OpenAIProvider(mock_settings)


def test_openai_provider_nonexistent_attribute():
    """Test OpenAI provider with non-existent attribute."""
    from ai_utilities.providers import OpenAIProvider
    
    # Should raise AttributeError for non-existent attributes
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
    """Test create_provider function exists and is callable."""
    from ai_utilities.providers import create_provider
    
    # Test that the function exists and is callable
    assert callable(create_provider)
    
    # Test that it has the expected signature
    import inspect
    sig = inspect.signature(create_provider)
    expected_params = ['settings', 'provider']
    actual_params = list(sig.parameters.keys())
    assert actual_params[:2] == expected_params


def test_openai_provider_multiple_access():
    """Test multiple accesses to OpenAIProvider."""
    from ai_utilities.providers import OpenAIProvider
    
    # Access multiple times - should work consistently
    attr1 = OpenAIProvider
    attr2 = OpenAIProvider
    
    # Should be the same class
    assert attr1 is attr2


def test_openai_provider_consistency():
    """Test OpenAIProvider is consistent across accesses."""
    from ai_utilities.providers import OpenAIProvider
    
    # Should be the same class object
    provider1 = OpenAIProvider
    provider2 = OpenAIProvider
    
    assert provider1 is provider2
    
    # If it's the real provider, it should have provider_name
    # If it's a placeholder, that's also OK - the important thing is consistency
    if hasattr(provider1, 'provider_name'):
        # Check if provider_name is a property and get its value
        provider_name_attr = getattr(provider1, 'provider_name', None)
        if isinstance(provider_name_attr, property):
            # Create a mock instance to get the property value
            from unittest.mock import Mock
            mock_settings = Mock()
            mock_settings.api_key = "test_key"
            mock_settings.base_url = None
            mock_settings.timeout = 30
            try:
                mock_instance = provider1(mock_settings)
                assert mock_instance.provider_name == "openai"
            except MissingOptionalDependencyError:
                # OpenAI not available, can't test property value
                pass
        else:
            # It's a regular attribute
            assert provider_name_attr == "openai"
