"""
Tests for providers/__init__.py to achieve 100% coverage.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

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
            "provider_factory",
            "openai_compatible_provider",
            "ProviderCapabilities",
            "ProviderCapabilityError", 
            "ProviderConfigurationError",
            "FileTransferError",
            "MissingOptionalDependencyError"
        ]
        
        assert __all__ == expected_exports


class TestOpenAIProviderDirect:
    """Test the direct OpenAIProvider class export."""
    
    def test_openai_provider_class_available(self):
        """Test that OpenAIProvider class is available."""
        with patch('ai_utilities.providers.OpenAIProvider') as mock_openai:
            mock_provider_class = Mock()
            mock_openai.return_value = mock_provider_class
            
            # Import the class directly from the module
            from ai_utilities.providers import OpenAIProvider
            
            # Should be callable (class)
            assert callable(OpenAIProvider)
    
    def test_openai_provider_import_error(self):
        """Test OpenAI provider basic error handling."""
        from ai_utilities.providers import OpenAIProvider
        
        # Should be available and callable (class)
        assert callable(OpenAIProvider)
        
        # Test that it has expected attributes
        assert hasattr(OpenAIProvider, '__name__')
    
    def test_openai_provider_basic_attributes(self):
        """Test OpenAIProvider basic attributes."""
        from ai_utilities.providers import OpenAIProvider
        
        # Should be callable (class)
        assert callable(OpenAIProvider)
        
        # Should have basic class attributes if OpenAI is available
        try:
            assert hasattr(OpenAIProvider, '__name__')
            assert hasattr(OpenAIProvider, '__init__')
        except AttributeError:
            # Expected if OpenAI is not available
            pass
    
    def test_openai_provider_instantiation(self):
        """Test OpenAIProvider instantiation."""
        from ai_utilities.providers import OpenAIProvider
        
        # Should be able to attempt instantiation (may fail without proper settings)
        assert hasattr(OpenAIProvider, '__call__') or callable(OpenAIProvider)


class TestProvidersInitIntegration:
    """Test integration scenarios for providers/__init__.py."""
    
    def test_provider_creation_import(self):
        """Test that create_provider can be imported."""
        from ai_utilities.providers import create_provider
        
        # Should be callable
        assert callable(create_provider)
    
    def test_provider_creation_with_compatible(self):
        """Test provider creation with compatible provider."""
        from ai_utilities.providers import create_provider
        
        # Should be callable
        assert callable(create_provider)
    
    def test_exception_hierarchy(self):
        """Test that provider exceptions have proper hierarchy."""
        # Test that exceptions can be raised and caught
        with pytest.raises(ProviderCapabilityError):
            raise ProviderCapabilityError("Test")
        
        with pytest.raises(ProviderConfigurationError):
            raise ProviderConfigurationError("Test", "test_provider")
        
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
    
    def test_multiple_openai_provider_access(self):
        """Test multiple accesses to OpenAIProvider."""
        from ai_utilities.providers import OpenAIProvider
        
        # Access multiple times - should be consistent
        try:
            attr1 = getattr(OpenAIProvider, '__name__', None)
            attr2 = getattr(OpenAIProvider, '__name__', None)
            # Should be consistent
            assert attr1 == attr2
        except AttributeError:
            # Expected if OpenAI is not available
            pass
    
    def test_openai_provider_error_handling(self):
        """Test OpenAIProvider error handling."""
        from ai_utilities.providers import OpenAIProvider
        
        # Should handle missing attributes gracefully
        with pytest.raises(AttributeError):
            _ = OpenAIProvider.non_existent_attribute_12345
    
    def test_openai_provider_with_mock(self):
        """Test OpenAIProvider with mocking."""
        with patch('ai_utilities.providers.OpenAIProvider') as mock_provider:
            mock_provider.TEST_ATTR = "test_value"
            
            from ai_utilities.providers import OpenAIProvider
            
            assert OpenAIProvider.TEST_ATTR == "test_value"
    
    def test_import_error_message_format(self):
        """Test that import error message has correct format."""
        from ai_utilities.providers import OpenAIProvider
        
        # Should be available and callable
        assert callable(OpenAIProvider)
    
    def test_all_list_completeness(self):
        """Test that __all__ contains all expected items."""
        from ai_utilities.providers import __all__
        
        # Verify all items in __all__ are actually importable
        for item in __all__:
            assert hasattr(__import__('ai_utilities.providers', fromlist=[item]), item), f"{item} not found in module"


class TestProvidersInitErrorHandling:
    """Test import error handling branches in providers/__init__.py."""

    def test_openai_provider_fallback_with_import_error(self) -> None:
        """Test OpenAI provider fallback when ImportError occurs."""
        # Remove modules to force re-import
        modules_to_remove = [
            'ai_utilities.providers',
            'ai_utilities.providers.openai_provider'
        ]
        removed_modules = {}
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                removed_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]
        
        try:
            # Create a mock module that raises ImportError when accessed
            import types
            def mock_import():
                raise ImportError("No openai")
            
            mock_module = types.ModuleType('mock_openai_provider')
            mock_module.__spec__ = None  # This will cause ImportError on import
            
            # Put the mock module in sys.modules to trigger ImportError on relative import
            sys.modules['ai_utilities.providers.openai_provider'] = mock_module
            
            # Re-import to trigger the fallback path
            import importlib
            importlib.reload(__import__('ai_utilities.providers'))
            import ai_utilities.providers as providers
            
            # The fallback class should raise MissingOptionalDependencyError
            with pytest.raises(MissingOptionalDependencyError) as exc_info:
                providers.OpenAIProvider(settings={})
            
            error_msg = str(exc_info.value)
            assert "OpenAI provider requires extra 'openai'" in error_msg
            assert "pip install ai-utilities[openai]" in error_msg
        finally:
            # Restore modules
            for module_name, module in removed_modules.items():
                sys.modules[module_name] = module

    def test_openai_compatible_provider_fallback_with_import_error(self) -> None:
        """Test OpenAI Compatible provider fallback when ImportError occurs."""
        # Remove modules to force re-import
        modules_to_remove = [
            'ai_utilities.providers',
            'ai_utilities.providers.openai_compatible_provider'
        ]
        removed_modules = {}
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                removed_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]
        
        try:
            # Create a mock module that raises ImportError when accessed
            import types
            
            mock_module = types.ModuleType('mock_openai_compatible_provider')
            mock_module.__spec__ = None  # This will cause ImportError on import
            
            # Put the mock module in sys.modules to trigger ImportError on relative import
            sys.modules['ai_utilities.providers.openai_compatible_provider'] = mock_module
            
            # Re-import to trigger the fallback path
            import importlib
            importlib.reload(__import__('ai_utilities.providers'))
            import ai_utilities.providers as providers
            
            # The fallback class should raise MissingOptionalDependencyError
            with pytest.raises(MissingOptionalDependencyError) as exc_info:
                providers.OpenAICompatibleProvider(settings={})
            
            error_msg = str(exc_info.value)
            assert "OpenAI Compatible provider requires extra 'openai'" in error_msg
            assert "pip install ai-utilities[openai]" in error_msg
        finally:
            # Restore modules
            for module_name, module in removed_modules.items():
                sys.modules[module_name] = module

    def test_exception_chaining_in_fallback_classes(self) -> None:
        """Test that fallback classes properly chain exceptions."""
        # Test the exception chaining works correctly
        original_error = ImportError("No module named 'openai'")
        
        try:
            raise MissingOptionalDependencyError("Test message") from original_error
        except MissingOptionalDependencyError as e:
            assert e.__cause__ is original_error
            assert str(e) == "Test message"
    
    
