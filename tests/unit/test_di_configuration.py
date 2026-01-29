"""Tests for dependency injection configuration context."""

import pytest

from ai_utilities.context.configuration import (
    ConfigurationContext,
    configuration_context,
    get_default_context,
    set_default_context,
    get_current_ai_settings,
    get_current_environment_provider,
    get_current_config_manager,
)
from ai_utilities.di.environment import EnvironmentProviderStub
from ai_utilities.config_models import AiSettings


class TestConfigurationContext:
    """Test the ConfigurationContext class."""
    
    def test_configuration_context_basic(self):
        """Test ConfigurationContext basic functionality."""
        env_provider = EnvironmentProviderStub({"AI_MODEL": "test-model"})
        
        with ConfigurationContext(environment_provider=env_provider) as context:
            # Test getting environment provider
            provider = context.get_environment_provider()
            assert provider is env_provider
            
            # Test getting config manager
            config_manager = context.get_config_manager()
            assert config_manager is not None
            
            # Test getting AI settings (simplified implementation)
            settings = context.get_ai_settings(model="test-model")
            assert isinstance(settings, AiSettings)
            assert settings.model == "test-model"
    
    def test_configuration_context_with_ai_settings(self):
        """Test ConfigurationContext with pre-configured AI settings."""
        test_settings = AiSettings(model="preset-model", temperature=0.5)
        
        with ConfigurationContext(ai_settings=test_settings) as context:
            settings = context.get_ai_settings()
            assert settings.model == "preset-model"
            assert settings.temperature == 0.5
    
    def test_configuration_context_additional_config(self):
        """Test ConfigurationContext additional configuration values."""
        with ConfigurationContext(custom_value="test", another_value=123) as context:
            # Test getting config values
            assert context.get_config("custom_value") == "test"
            assert context.get_config("another_value") == 123
            assert context.get_config("missing", "default") == "default"
            
            # Test updating config
            context.update_config(custom_value="updated", new_value="new")
            assert context.get_config("custom_value") == "updated"
            assert context.get_config("new_value") == "new"
    
    def test_configuration_context_nesting(self):
        """Test ConfigurationContext nesting behavior."""
        outer_env = EnvironmentProviderStub({"AI_MODEL": "outer-model"})
        inner_env = EnvironmentProviderStub({"AI_MODEL": "inner-model"})
        
        with ConfigurationContext(environment_provider=outer_env) as outer_context:
            # Should use outer context
            assert ConfigurationContext.current() is outer_context
            settings = outer_context.get_ai_settings()
            assert settings.model == "outer-model"
            
            with ConfigurationContext(environment_provider=inner_env) as inner_context:
                # Should use inner context
                assert ConfigurationContext.current() is inner_context
                settings = inner_context.get_ai_settings()
                assert settings.model == "inner-model"
            
            # Back to outer context
            assert ConfigurationContext.current() is outer_context
            settings = outer_context.get_ai_settings()
            assert settings.model == "outer-model"
        
        # No context set
        assert ConfigurationContext.current() is None
    
    def test_configuration_context_require_current(self):
        """Test ConfigurationContext.require_current method."""
        # Should raise error when no context is set
        with pytest.raises(RuntimeError, match="No configuration context is set"):
            ConfigurationContext.require_current()
        
        # Should return context when set
        with ConfigurationContext() as context:
            result = ConfigurationContext.require_current()
            assert result is context
    
    def test_default_context_management(self):
        """Test default configuration context management."""
        # Test getting default context
        context1 = get_default_context()
        context2 = get_default_context()
        assert context1 is context2  # Should be same instance
        
        # Test setting default context
        new_context = ConfigurationContext(custom_value="test")
        set_default_context(new_context)
        
        context3 = get_default_context()
        assert context3 is new_context
        assert context3 is not context1
    
    def test_configuration_context_function(self):
        """Test configuration_context convenience function."""
        env_provider = EnvironmentProviderStub({"AI_MODEL": "func-model"})
        
        with configuration_context(environment_provider=env_provider) as context:
            assert isinstance(context, ConfigurationContext)
            assert context.get_environment_provider() is env_provider
            
            settings = context.get_ai_settings()
            assert settings.model == "func-model"
    
    def test_backward_compatibility_functions(self):
        """Test backward compatibility functions."""
        env_provider = EnvironmentProviderStub({"AI_MODEL": "compat-model"})
        
        # Test without context (uses default)
        settings = get_current_ai_settings()
        assert isinstance(settings, AiSettings)
        
        provider = get_current_environment_provider()
        assert isinstance(provider, EnvironmentProviderStub) or hasattr(provider, 'get')
        
        config_manager = get_current_config_manager()
        assert config_manager is not None
        
        # Test with context
        with ConfigurationContext(environment_provider=env_provider) as context:
            settings = get_current_ai_settings()
            assert settings.model == "compat-model"
            
            provider = get_current_environment_provider()
            assert provider is env_provider
            
            config_manager = get_current_config_manager()
            assert config_manager is context.get_config_manager()


class TestConfigurationContextIntegration:
    """Integration tests for configuration context."""
    
    def test_context_with_ai_settings_integration(self):
        """Test ConfigurationContext integration with AiSettings."""
        env_provider = EnvironmentProviderStub({
            "AI_MODEL": "env-model",
            "AI_TEMPERATURE": "0.8",
            "AI_API_KEY": "test-key"
        })
        
        with ConfigurationContext(environment_provider=env_provider) as context:
            # Test getting AI settings from environment
            settings = context.get_ai_settings()
            assert settings.model == "env-model"
            assert settings.temperature == 0.8
            assert settings.api_key == "test-key"
            
            # Test overriding with kwargs
            settings = context.get_ai_settings(model="override-model", temperature=0.5)
            assert settings.model == "override-model"  # Override takes precedence
            assert settings.temperature == 0.5  # Override takes precedence
            assert settings.api_key == "test-key"  # From environment
    
    def test_context_caching_behavior(self):
        """Test ConfigurationContext AI settings caching."""
        env_provider = EnvironmentProviderStub({"AI_MODEL": "cached-model"})
        
        with ConfigurationContext(environment_provider=env_provider) as context:
            # First call should create and cache settings
            settings1 = context.get_ai_settings()
            assert settings1.model == "cached-model"
            
            # Second call should return cached instance
            settings2 = context.get_ai_settings()
            assert settings1 is settings2  # Same instance
            
            # Override with kwargs should create new instance
            settings3 = context.get_ai_settings(model="new-model")
            assert settings3.model == "new-model"
            assert settings3 is not settings1
    
    def test_context_thread_safety(self):
        """Test ConfigurationContext thread safety."""
        import threading
        import time
        
        results = {}
        
        def worker(thread_id):
            """Worker function for threading test."""
            env_provider = EnvironmentProviderStub({"AI_MODEL": f"thread-{thread_id}-model"})
            
            with ConfigurationContext(environment_provider=env_provider) as context:
                settings = context.get_ai_settings()
                results[thread_id] = settings.model
                time.sleep(0.1)  # Small delay to ensure interleaving
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Each thread should have its own settings
        assert len(results) == 3
        for i in range(3):
            assert results[i] == f"thread-{i}-model"
    
    def test_context_error_handling(self):
        """Test ConfigurationContext error handling."""
        # Test that context is properly restored even with exceptions
        outer_context = ConfigurationContext(outer_value="test")
        
        try:
            with outer_context:
                assert ConfigurationContext.current() is outer_context
                
                # Create inner context that will raise exception
                inner_context = ConfigurationContext(inner_value="inner")
                with inner_context:
                    assert ConfigurationContext.current() is inner_context
                    raise ValueError("Test exception")
        
        except ValueError:
            pass  # Expected
        
        # Context should be properly restored
        assert ConfigurationContext.current() is None
