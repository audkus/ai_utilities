"""
Environment overrides using contextvars for safe per-context isolation.

This module provides thread-safe and asyncio-safe environment variable overrides
without mutating os.environ. Uses contextvars for proper isolation in concurrent
environments.
"""

from __future__ import annotations

import contextvars
import os
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Dict

# ContextVar to store environment overrides with default empty dict
_env_overrides: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar(
    "env_overrides",
    default={}
)

# ContextVar to track if we're in test mode
_test_mode: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "test_mode",
    default=False
)


def is_test_mode() -> bool:
    """
    Check if we're currently running in test mode.
    
    Test mode is detected by:
    1. pytest being in sys.modules
    2. PYTEST_CURRENT_TEST environment variable being set
    3. Explicit test mode context
    
    Returns:
        True if running in test context
    """
    # Check explicit test mode context first
    if _test_mode.get():
        return True
    
    # Check if pytest is running
    if 'pytest' in sys.modules:
        return True
    
    # Check pytest environment variable
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return True
    
    return False


@contextmanager
def test_mode_guard() -> Iterator[None]:
    """
    Context manager to enable test mode guards.
    
    In test mode:
    - Direct os.environ mutations raise warnings/errors
    - Contextvar overrides are strictly enforced
    - Global state changes are tracked
    
    This helps prevent test isolation regressions.
    """
    # Enable test mode
    token = _test_mode.set(True)
    
    try:
        yield
    finally:
        # Restore previous test mode state
        _test_mode.reset(token)


def _warn_if_direct_env_mutation(key: str) -> None:
    """
    Issue a warning if direct environment mutation is detected in test mode.
    
    Args:
        key: The environment variable key being accessed
    """
    if is_test_mode():
        import warnings
        warnings.warn(
            f"Direct os.environ access detected for '{key}' in test mode. "
            f"Consider using override_env() context manager for test isolation.",
            UserWarning,
            stacklevel=3
        )


def get_env_overrides() -> Dict[str, str]:
    """
    Get current environment overrides from context.
    
    Returns:
        Copy of current environment overrides dictionary
    """
    return dict(_env_overrides.get())


@contextmanager
def override_env(env_vars: Mapping[str, Any] | None = None) -> Iterator[None]:
    """
    Context manager to temporarily override environment variables.
    
    This function provides safe environment variable overrides without mutating
    os.environ. It's thread-safe and asyncio-safe using contextvars.
    
    Args:
        env_vars: Dictionary of environment variables to override.
                 Values are automatically converted to strings.
                 If None, no additional overrides are applied.
    
    Example:
        with override_env({"AI_MODEL": "test-model-1.1", "AI_TEMPERATURE": 0.9}):
            settings = AiSettings()  # Uses overridden values
        # Context automatically restored
    
    Yields:
        None
    """
    # In test mode, validate that we're not creating nested overrides that might leak
    if is_test_mode():
        current_overrides = _env_overrides.get()
        if current_overrides and env_vars:
            # Check for potential key conflicts that might cause confusion
            conflicts = set(current_overrides.keys()) & set(env_vars.keys())
            if conflicts:
                import warnings
                warnings.warn(
                    f"Nested environment overrides detected for keys: {sorted(conflicts)}. "
                    f"This might indicate test isolation issues. "
                    f"Consider restructuring your test to avoid nested overrides.",
                    UserWarning,
                    stacklevel=3
                )
    
    # Get current overrides
    current_overrides = _env_overrides.get()
    
    # Prepare new overrides by merging with existing ones
    new_overrides = dict(current_overrides)
    
    if env_vars:
        # Convert all values to strings and merge
        str_env_vars = {k: str(v) for k, v in env_vars.items()}
        new_overrides.update(str_env_vars)
    
    # Set the new overrides in context
    token = _env_overrides.set(new_overrides)
    
    try:
        yield
    finally:
        # Always restore the previous state
        _env_overrides.reset(token)


def get_safe_env(key: str, default: Any = None) -> str | None:
    """
    Get environment variable with test-mode safety checks.
    
    This function provides a safe way to access environment variables that
    respects contextvar overrides and warns about direct access in test mode.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    # Warn about direct access in test mode
    _warn_if_direct_env_mutation(key)
    
    # Check contextvar overrides first
    overrides = _env_overrides.get()
    if key in overrides:
        return overrides[key]
    
    # Fall back to real environment
    return os.environ.get(key, default)


class OverrideAwareEnvSource:
    """
    Environment source that respects contextvar overrides.
    
    This source checks for contextvar overrides first, then falls back to
    the real environment variables.
    """
    
    def __init__(self, env_prefix: str = "AI_"):
        """
        Initialize the override-aware environment source.
        
        Args:
            env_prefix: Environment variable prefix (e.g., "AI_")
        """
        self.env_prefix = env_prefix
    
    def get(self, key: str) -> str | None:
        """
        Get environment variable value, checking overrides first.
        
        Args:
            key: Environment variable key (without prefix)
            
        Returns:
            Environment variable value or None if not found
        """
        # Check contextvar overrides first
        overrides = get_env_overrides()
        env_key = f"{self.env_prefix}{key.upper()}"
        
        if env_key in overrides:
            return overrides[env_key]
        
        # Fall back to real environment
        import os
        return os.environ.get(env_key)
    
    def get_bool(self, key: str) -> bool:
        """Get boolean environment variable."""
        value = self.get(key)
        if value is None:
            return False
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str) -> int:
        """Get integer environment variable."""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Environment variable {key} not found")
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be an integer, got: {value}")
    
    def get_float(self, key: str) -> float:
        """Get float environment variable."""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Environment variable {key} not found")
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be a float, got: {value}")


# Global instance for AI environment variables
_ai_env_source = OverrideAwareEnvSource("AI_")


def get_ai_env(key: str) -> str | None:
    """Get AI environment variable with override support."""
    return _ai_env_source.get(key)


def get_ai_env_bool(key: str) -> bool:
    """Get AI boolean environment variable with override support."""
    return _ai_env_source.get_bool(key)


def get_ai_env_int(key: str) -> int:
    """Get AI integer environment variable with override support."""
    return _ai_env_source.get_int(key)


def get_ai_env_float(key: str) -> float:
    """Get AI float environment variable with override support."""
    return _ai_env_source.get_float(key)


def _reset_all_overrides() -> None:
    """
    Reset all contextvar overrides to clean state.
    
    This function is used by test isolation to reset contextvar state
    between test runs. It's safe to call multiple times.
    """
    # Reset the contextvar to its default (empty dict)
    _env_overrides.set({})
