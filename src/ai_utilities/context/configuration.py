"""
Configuration context management for dependency injection.

This module provides context management for configuration dependencies,
eliminating the need for global singletons.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from ..config_models import AiSettings
from ..di.environment import EnvironmentProvider, get_default_environment_provider
from ..ai_config_manager import AIConfigManager


class ConfigurationContext:
    """
    Context manager for configuration dependencies.
    
    This context provides explicit dependency injection for configuration,
    environment access, and other services, eliminating global state.
    """
    
    # Context variables for thread-local storage
    _config_context: contextvars.ContextVar[ConfigurationContext] = contextvars.ContextVar(
        "config_context",
        default=None
    )
    
    def __init__(
        self,
        config_manager: Optional[AIConfigManager] = None,
        environment_provider: Optional[EnvironmentProvider] = None,
        ai_settings: Optional[AiSettings] = None,
        **kwargs
    ):
        """
        Initialize configuration context.
        
        Args:
            config_manager: Configuration manager instance
            environment_provider: Environment provider instance
            ai_settings: AI settings instance
            **kwargs: Additional configuration values
        """
        self.config_manager = config_manager or AIConfigManager()
        self.environment_provider = environment_provider or get_default_environment_provider()
        self.ai_settings = ai_settings
        self.additional_config = kwargs
        
        # Store previous context for restoration
        self._previous_context = None
        self._token = None
    
    def __enter__(self) -> ConfigurationContext:
        """Enter the configuration context."""
        # Store previous context
        self._previous_context = self._config_context.get()
        
        # Set this context as current
        self._token = self._config_context.set(self)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the configuration context."""
        # Restore previous context
        if self._token is not None:
            self._config_context.reset(self._token)
    
    def get_ai_settings(self, **kwargs) -> AiSettings:
        """
        Get AI settings from this context.
        
        Args:
            **kwargs: Additional settings to override
            
        Returns:
            AiSettings instance
        """
        # If kwargs are provided, always create new settings (don't use cache)
        if kwargs:
            # Get environment variables from the environment provider
            env_vars = self.environment_provider.get_all()
            
            # Map environment variables to AiSettings constructor arguments
            ai_settings_kwargs = {}
            for key, value in env_vars.items():
                if key.startswith('AI_'):
                    setting_key = key[3:].lower()
                    ai_settings_kwargs[setting_key] = value
            
            # Add kwargs (these take precedence)
            ai_settings_kwargs.update(kwargs)
            
            # Create new AiSettings without caching
            return AiSettings(_env_file=None, **ai_settings_kwargs)
        
        # No kwargs - use cached settings if available
        if self.ai_settings is not None:
            return self.ai_settings
        
        # Get environment variables from the environment provider
        env_vars = self.environment_provider.get_all()
        
        # Map environment variables to AiSettings constructor arguments
        ai_settings_kwargs = {}
        for key, value in env_vars.items():
            if key.startswith('AI_'):
                setting_key = key[3:].lower()
                ai_settings_kwargs[setting_key] = value
        
        # Create AiSettings using the environment provider's variables
        settings = AiSettings(_env_file=None, **ai_settings_kwargs)
        
        # Cache for future use (only when no kwargs)
        self.ai_settings = settings
        return settings
    
    def get_environment_provider(self) -> EnvironmentProvider:
        """
        Get the environment provider from this context.
        
        Returns:
            EnvironmentProvider instance
        """
        return self.environment_provider
    
    def get_config_manager(self) -> AIConfigManager:
        """
        Get the configuration manager from this context.
        
        Returns:
            AIConfigManager instance
        """
        return self.config_manager
    
    def update_config(self, **kwargs) -> None:
        """
        Update additional configuration values.
        
        Args:
            **kwargs: Configuration values to update
        """
        self.additional_config.update(kwargs)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get additional configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        return self.additional_config.get(key, default)
    
    @classmethod
    def current(cls) -> Optional[ConfigurationContext]:
        """
        Get the current configuration context.
        
        Returns:
            Current ConfigurationContext or None if not set
        """
        return cls._config_context.get()
    
    @classmethod
    def require_current(cls) -> ConfigurationContext:
        """
        Get the current configuration context, raising an error if not set.
        
        Returns:
            Current ConfigurationContext
            
        Raises:
            RuntimeError: If no configuration context is set
        """
        current = cls.current()
        if current is None:
            raise RuntimeError(
                "No configuration context is set. Use ConfigurationContext() to create one."
            )
        return current


# Global default context (for backward compatibility)
_default_context: Optional[ConfigurationContext] = None


def get_default_context() -> ConfigurationContext:
    """
    Get the default configuration context.
    
    Returns:
        Default ConfigurationContext instance
    """
    global _default_context
    if _default_context is None:
        _default_context = ConfigurationContext()
    return _default_context


def set_default_context(context: ConfigurationContext) -> None:
    """
    Set the default configuration context.
    
    Args:
        context: Configuration context to use as default
    """
    global _default_context
    _default_context = context


@contextmanager
def configuration_context(
    config_manager: Optional[AIConfigManager] = None,
    environment_provider: Optional[EnvironmentProvider] = None,
    ai_settings: Optional[AiSettings] = None,
    **kwargs
) -> Generator[ConfigurationContext, None, None]:
    """
    Context manager for configuration dependencies.
    
    This is a convenience function that creates and manages a ConfigurationContext.
    
    Args:
        config_manager: Configuration manager instance
        environment_provider: Environment provider instance
        ai_settings: AI settings instance
        **kwargs: Additional configuration values
        
    Yields:
        ConfigurationContext instance
    """
    with ConfigurationContext(
        config_manager=config_manager,
        environment_provider=environment_provider,
        ai_settings=ai_settings,
        **kwargs
    ) as context:
        yield context


# Backward compatibility functions
def get_current_ai_settings(**kwargs) -> AiSettings:
    """
    Get AI settings from current context or default.
    
    Args:
        **kwargs: Additional settings to override
        
    Returns:
        AiSettings instance
    """
    current = ConfigurationContext.current()
    if current is not None:
        return current.get_ai_settings(**kwargs)
    
    # Fall back to default context
    return get_default_context().get_ai_settings(**kwargs)


def get_current_environment_provider() -> EnvironmentProvider:
    """
    Get environment provider from current context or default.
    
    Returns:
        EnvironmentProvider instance
    """
    current = ConfigurationContext.current()
    if current is not None:
        return current.get_environment_provider()
    
    # Fall back to default context
    return get_default_context().get_environment_provider()


def get_current_config_manager() -> AIConfigManager:
    """
    Get configuration manager from current context or default.
    
    Returns:
        AIConfigManager instance
    """
    current = ConfigurationContext.current()
    if current is not None:
        return current.get_config_manager()
    
    # Fall back to default context
    return get_default_context().get_config_manager()
