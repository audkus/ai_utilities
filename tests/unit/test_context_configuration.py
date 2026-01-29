"""Tests for context configuration management."""

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


class TestConfigurationContext:
    """Test ConfigurationContext class and functions."""
    
    def test_configuration_context_creation(self):
        """Test creating a configuration context."""
        context = ConfigurationContext()
        assert context is not None
    
    def test_configuration_context_manager(self):
        """Test configuration context as context manager."""
        with configuration_context() as ctx:
            assert ctx is not None
    
    def test_get_default_context(self):
        """Test getting default context."""
        context = get_default_context()
        assert context is not None
    
    def test_set_default_context(self):
        """Test setting default context."""
        new_context = ConfigurationContext()
        set_default_context(new_context)
        assert get_default_context() is new_context
    
    def test_get_current_ai_settings(self):
        """Test getting current AI settings."""
        with configuration_context() as ctx:
            settings = get_current_ai_settings()
            assert settings is not None
    
    def test_get_current_environment_provider(self):
        """Test getting current environment provider."""
        with configuration_context() as ctx:
            provider = get_current_environment_provider()
            assert provider is not None
    
    def test_get_current_config_manager(self):
        """Test getting current config manager."""
        with configuration_context() as ctx:
            manager = get_current_config_manager()
            assert manager is not None
