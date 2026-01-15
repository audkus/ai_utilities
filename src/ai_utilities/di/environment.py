"""
Environment provider interfaces and implementations.

This module provides abstractions for environment variable access that
support dependency injection and testing without global state.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..env_overrides import get_env_overrides


class EnvironmentProvider(ABC):
    """Abstract interface for environment variable access."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> str | None:
        """
        Get environment variable value.
        
        Args:
            key: Environment variable key
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        pass
    
    @abstractmethod
    def get_all(self, prefix: str = "") -> Dict[str, str]:
        """
        Get all environment variables with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter variables
            
        Returns:
            Dictionary of environment variables
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """
        Set environment variable value.
        
        Args:
            key: Environment variable key
            value: Value to set
        """
        pass
    
    @abstractmethod
    def clear(self, key: str) -> None:
        """
        Clear environment variable.
        
        Args:
            key: Environment variable key to clear
        """
        pass


class ContextVarEnvironmentProvider(EnvironmentProvider):
    """
    Environment provider that respects contextvar overrides.
    
    This provider checks contextvar overrides first, then falls back
    to the real environment variables. This enables proper test
    isolation without global state mutations.
    """
    
    def __init__(self, warn_on_direct_access: bool = True):
        """
        Initialize the environment provider.
        
        Args:
            warn_on_direct_access: Whether to warn about direct access in test mode
        """
        self.warn_on_direct_access = warn_on_direct_access
    
    def get(self, key: str, default: Any = None) -> str | None:
        """Get environment variable with contextvar override support."""
        # Check contextvar overrides first
        overrides = get_env_overrides()
        if key in overrides:
            return overrides[key]
        
        # Warn about direct access if enabled
        if self.warn_on_direct_access:
            self._warn_if_direct_access(key)
        
        # Fall back to real environment
        return os.environ.get(key, default)
    
    def get_all(self, prefix: str = "") -> Dict[str, str]:
        """Get all environment variables with contextvar overrides applied."""
        # Get contextvar overrides
        overrides = get_env_overrides()
        
        # Get real environment
        real_env = dict(os.environ)
        
        # Apply overrides (contextvar takes precedence)
        combined = {**real_env, **overrides}
        
        # Filter by prefix if specified
        if prefix:
            return {k: v for k, v in combined.items() if k.startswith(prefix)}
        
        return combined
    
    def set(self, key: str, value: str) -> None:
        """
        Set environment variable in contextvar overrides.
        
        Note: This only affects the current context, not the real environment.
        """
        from ..env_overrides import override_env
        
        # Use override_env to set the value in current context
        # This is a temporary solution - in the future we'll have
        # a more direct way to manipulate contextvar state
        current_overrides = get_env_overrides()
        new_overrides = {**current_overrides, key: value}
        
        # This is a bit of a hack since we can't directly modify
        # the contextvar from outside the override_env context
        # For now, we'll document this limitation
        raise NotImplementedError(
            "Direct setting not yet implemented. Use override_env() context manager."
        )
    
    def clear(self, key: str) -> None:
        """Clear environment variable from contextvar overrides."""
        # Similar to set(), this would need direct contextvar manipulation
        raise NotImplementedError(
            "Direct clearing not yet implemented. Use override_env() context manager."
        )
    
    def _warn_if_direct_access(self, key: str) -> None:
        """Issue warning about direct environment access in test mode."""
        # Import here to avoid circular imports
        try:
            from ..env_overrides import is_test_mode
            if is_test_mode():
                import warnings
                warnings.warn(
                    f"Direct environment access detected for '{key}' in test mode. "
                    f"Consider using ContextVarEnvironmentProvider with proper context.",
                    UserWarning,
                    stacklevel=3
                )
        except ImportError:
            # If we can't import env_overrides, skip the warning
            pass


class StandardEnvironmentProvider(EnvironmentProvider):
    """
    Standard environment provider that directly accesses os.environ.
    
    This provider doesn't respect contextvar overrides and is useful
    for scenarios where you need direct access to the real environment.
    """
    
    def get(self, key: str, default: Any = None) -> str | None:
        """Get environment variable directly from os.environ."""
        return os.environ.get(key, default)
    
    def get_all(self, prefix: str = "") -> Dict[str, str]:
        """Get all environment variables with optional prefix filter."""
        env = dict(os.environ)
        if prefix:
            return {k: v for k, v in env.items() if k.startswith(prefix)}
        return env
    
    def set(self, key: str, value: str) -> None:
        """Set environment variable in os.environ."""
        os.environ[key] = value
    
    def clear(self, key: str) -> None:
        """Clear environment variable from os.environ."""
        if key in os.environ:
            del os.environ[key]


class TestEnvironmentProvider(EnvironmentProvider):
    """
    Test environment provider with controlled state.
    
    This provider maintains its own internal state for testing
    scenarios without affecting the real environment.
    """
    
    def __init__(self, initial_state: Dict[str, str] = None):
        """
        Initialize test environment provider.
        
        Args:
            initial_state: Initial environment state
        """
        self._env = dict(initial_state or {})
    
    def get(self, key: str, default: Any = None) -> str | None:
        """Get environment variable from test state."""
        return self._env.get(key, default)
    
    def get_all(self, prefix: str = "") -> Dict[str, str]:
        """Get all environment variables with optional prefix filter."""
        if prefix:
            return {k: v for k, v in self._env.items() if k.startswith(prefix)}
        return dict(self._env)
    
    def set(self, key: str, value: str) -> None:
        """Set environment variable in test state."""
        self._env[key] = value
    
    def clear(self, key: str) -> None:
        """Clear environment variable from test state."""
        if key in self._env:
            del self._env[key]
    
    def reset(self, new_state: Dict[str, str] = None) -> None:
        """Reset environment state."""
        self._env = dict(new_state or {})


# Default provider for backward compatibility
_default_provider: Optional[EnvironmentProvider] = None


def get_default_environment_provider() -> EnvironmentProvider:
    """
    Get the default environment provider.
    
    Returns:
        ContextVarEnvironmentProvider instance
    """
    global _default_provider
    if _default_provider is None:
        _default_provider = ContextVarEnvironmentProvider()
    return _default_provider


def set_default_environment_provider(provider: EnvironmentProvider) -> None:
    """
    Set the default environment provider.
    
    Args:
        provider: Environment provider to use as default
    """
    global _default_provider
    _default_provider = provider


# Convenience functions for backward compatibility
def get_env(key: str, default: Any = None) -> str | None:
    """
    Get environment variable using default provider.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    return get_default_environment_provider().get(key, default)


def get_all_env(prefix: str = "") -> Dict[str, str]:
    """
    Get all environment variables using default provider.
    
    Args:
        prefix: Optional prefix to filter variables
        
    Returns:
        Dictionary of environment variables
    """
    return get_default_environment_provider().get_all(prefix)
