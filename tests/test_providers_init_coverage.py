"""
Tests for providers/__init__.py to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch

from ai_utilities.providers import (
    BaseProvider, OpenAIProvider, OpenAICompatibleProvider, create_provider,
    ProviderCapabilities, ProviderCapabilityError, ProviderConfigurationError,
    FileTransferError, MissingOptionalDependencyError
)


class TestProvidersInitImports:
    """Test imports and exports in providers/__init__.py."""
    
    def test_base_provider_import(self):
        """Test BaseProvider import."""
        from ai_utilities.providers.base_provider import BaseProvider
        assert BaseProvider is not None
    
    def test_openai_compatible_provider_import(self):
        """Test OpenAICompatibleProvider import."""
        from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
        assert OpenAICompatibleProvider is not None
    
    def test_create_provider_import(self):
        """Test create_provider import."""
        from ai_utilities.providers.provider_factory import create_provider
        assert create_provider is not None
    
    def test_provider_capabilities_import(self):
        """Test ProviderCapabilities import."""
        from ai_utilities.providers.provider_capabilities import ProviderCapabilities
        assert ProviderCapabilities is not None
    
    def test_provider_exceptions_import(self):
        """Test provider exceptions import."""
        from ai_utilities.providers.provider_exceptions import (
            ProviderCapabilityError, ProviderConfigurationError, FileTransferError,
            MissingOptionalDependencyError
        )
        assert ProviderCapabilityError is not None
        assert ProviderConfigurationError is not None
        assert FileTransferError is not None
        assert MissingOptionalDependencyError is not None
    
    def test_all_exports(self):
        """Test __all__ exports."""
        from ai_utilities.providers import __all__
        
        expected_exports = [
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
        
        assert __all__ == expected_exports


class TestLazyOpenAIProvider:
    """Test the lazy OpenAIProvider loading mechanism."""
    
    def test_get_openai_provider_success(self):
        """Test successful OpenAI provider loading."""
        # This tests the internal _get_openai_provider function
        with patch('ai_utilities.providers.OpenAIProvider') as mock_openai:
            mock_provider_class = Mock()
            mock_openai.return_value = mock_provider_class
            
            # Import the function directly from the module
            from ai_utilities.providers import _get_openai_provider
            
            result = _get_openai_provider()
            
            assert result == mock_provider_class
            mock_openai.assert_called_once()
    
    def test_get_openai_provider_import_error(self):
        """Test OpenAI provider loading with import error."""
        with patch('ai_utilities.providers.OpenAIProvider', side_effect=ImportError("No module named 'openai'")), \
             patch('ai_utilities.providers.MissingOptionalDependencyError') as mock_error:
            
            mock_error_instance = Exception("Missing dependency")
            mock_error.return_value = mock_error_instance
            
            from ai_utilities.providers import _get_openai_provider
            
            with pytest.raises(Exception):
                _get_openai_provider()
            
            mock_error.assert_called_once_with(
                "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
            )
    
    def test_lazy_openai_provider_attribute_access(self):
        """Test LazyOpenAIProvider attribute access."""
        with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
            mock_provider_class = Mock()
            mock_attribute = Mock()
            mock_provider_class.some_attribute = mock_attribute
            mock_get_provider.return_value = mock_provider_class
            
            # Access the LazyOpenAIProvider instance
            from ai_utilities.providers import OpenAIProvider
            
            result = OpenAIProvider.some_attribute
            
            assert result == mock_attribute
            mock_get_provider.assert_called_once()
    
    def test_lazy_openai_provider_method_access(self):
        """Test LazyOpenAIProvider method access."""
        with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
            mock_provider_class = Mock()
            mock_method = Mock(return_value="method_result")
            mock_provider_class.some_method = mock_method
            mock_get_provider.return_value = mock_provider_class
            
            from ai_utilities.providers import OpenAIProvider
            
            result = OpenAIProvider.some_method("arg1", kwarg1="value1")
            
            assert result == "method_result"
            mock_method.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_lazy_openai_provider_class_access(self):
        """Test LazyOpenAIProvider class-level access."""
        with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
            mock_provider_class = Mock()
            mock_class_attribute = "class_value"
            mock_provider_class.CLASS_ATTRIBUTE = mock_class_attribute
            mock_get_provider.return_value = mock_provider_class
            
            from ai_utilities.providers import OpenAIProvider
            
            result = OpenAIProvider.CLASS_ATTRIBUTE
            
            assert result == mock_class_attribute
    
    def test_lazy_openai_provider_instantiation(self):
        """Test LazyOpenAIProvider instantiation."""
        with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
            mock_provider_class = Mock()
            mock_instance = Mock()
            mock_provider_class.return_value = mock_instance
            mock_get_provider.return_value = mock_provider_class
            
            from ai_utilities.providers import OpenAIProvider
            
            result = OpenAIProvider("arg1", kwarg1="value1")
            
            assert result == mock_instance
            mock_provider_class.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_lazy_openai_provider_getattr_error(self):
        """Test LazyOpenAIProvider getattr with non-existent attribute."""
        with patch('ai_utilities.providers._get_openai_provider') as mock_get_provider:
            mock_provider_class = Mock()
            # Remove the attribute to trigger AttributeError
            del mock_provider_class.non_existent_attribute
            mock_get_provider.return_value = mock_provider_class
            
            from ai_utilities.providers import OpenAIProvider
            
            with pytest.raises(AttributeError):
                _ = OpenAIProvider.non_existent_attribute


class TestProvidersInitIntegration:
    """Test integration scenarios for providers/__init__.py."""
    
    def test_provider_creation_with_openai_available(self):
        """Test provider creation when OpenAI is available."""
        with patch('ai_utilities.providers.create_provider') as mock_create:
            mock_provider = Mock()
            mock_create.return_value = mock_provider
            
            result = create_provider({"provider": "openai"})
            
            assert result == mock_provider
    
    def test_provider_creation_with_compatible(self):
        """Test provider creation with compatible provider."""
        with patch('ai_utilities.providers.create_provider') as mock_create:
            mock_provider = Mock()
            mock_create.return_value = mock_provider
            
            result = create_provider({"provider": "openai_compatible"})
            
            assert result == mock_provider
    
    def test_exception_hierarchy(self):
        """Test that provider exceptions have proper hierarchy."""
        # Test that exceptions can be raised and caught
        with pytest.raises(ProviderCapabilityError):
            raise ProviderCapabilityError("Test")
        
        with pytest.raises(ProviderConfigurationError):
            raise ProviderConfigurationError("Test")
        
        with pytest.raises(FileTransferError):
            raise FileTransferError("upload", "test", Exception("test"))
        
        with pytest.raises(MissingOptionalDependencyError):
            raise MissingOptionalDependencyError("Test dependency")
    
    def test_provider_capabilities_usage(self):
        """Test ProviderCapabilities can be used."""
        capabilities = ProviderCapabilities()
        assert capabilities is not None
    
    def test_base_provider_as_abstract(self):
        """Test BaseProvider can be used as abstract base."""
        # Can't instantiate abstract base class directly
        with pytest.raises(TypeError):
            BaseProvider()
    
    def test_openai_compatible_provider_instantiation(self):
        """Test OpenAICompatibleProvider can be instantiated."""
        with patch('ai_utilities.providers.OpenAICompatibleProvider.__init__', return_value=None):
            provider = OpenAICompatibleProvider()
            assert provider is not None


class TestProvidersInitEdgeCases:
    """Test edge cases in providers/__init__.py."""
    
    def test_multiple_lazy_access(self):
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
    
    def test_lazy_provider_with_none_return(self):
        """Test LazyOpenAIProvider when _get_openai_provider returns None."""
        with patch('ai_utilities.providers._get_openai_provider', return_value=None):
            from ai_utilities.providers import OpenAIProvider
            
            # This should raise an AttributeError when trying to get attribute from None
            with pytest.raises(AttributeError):
                _ = OpenAIProvider.some_attribute
    
    def test_lazy_provider_with_exception_in_get_provider(self):
        """Test LazyOpenAIProvider when _get_openai_provider raises exception."""
        with patch('ai_utilities.providers._get_openai_provider', side_effect=RuntimeError("Provider error")):
            from ai_utilities.providers import OpenAIProvider
            
            # Should propagate the RuntimeError
            with pytest.raises(RuntimeError, match="Provider error"):
                _ = OpenAIProvider.some_attribute
    
    def test_import_error_message_format(self):
        """Test that import error message has correct format."""
        with patch('ai_utilities.providers.OpenAIProvider', side_effect=ImportError("No openai")), \
             patch('ai_utilities.providers.MissingOptionalDependencyError') as mock_error_class:
            
            mock_error = MissingOptionalDependencyError("Test message")
            mock_error_class.return_value = mock_error
            
            from ai_utilities.providers import _get_openai_provider
            
            try:
                _get_openai_provider()
            except MissingOptionalDependencyError as e:
                # Verify the error was created with correct message
                mock_error_class.assert_called_once_with(
                    "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                )
    
    def test_all_list_completeness(self):
        """Test that __all__ contains all expected items."""
        from ai_utilities.providers import __all__
        
        # Verify all items in __all__ are actually importable
        for item in __all__:
            assert hasattr(__import__('ai_utilities.providers', fromlist=[item]), item), f"{item} not found in module"
    
    def test_no_extra_exports(self):
        """Test that no unexpected items are exported."""
        import ai_utilities.providers as providers_module
        
        # Get all public attributes (not starting with _)
        public_attrs = [attr for attr in dir(providers_module) if not attr.startswith('_')]
        
        # Remove module attributes that shouldn't be in __all__
        expected_attrs = set(providers_module.__all__)
        unexpected_attrs = set(public_attrs) - expected_attrs
        
        # Should only have internal/private attributes outside __all__
        for attr in unexpected_attrs:
            assert attr.startswith('_'), f"Unexpected public export: {attr}"
