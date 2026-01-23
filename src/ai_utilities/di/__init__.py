"""
Dependency injection framework for ai_utilities.

This package provides abstractions for environment access, configuration,
metrics, and other services that support dependency injection and testing
without global state.
"""

from .environment import (
    EnvironmentProvider,
    ContextVarEnvironmentProvider,
    StandardEnvironmentProvider,
    EnvironmentProviderStub,
    get_default_environment_provider,
    set_default_environment_provider,
    get_env,
    get_all_env,
)

__all__ = [
    "EnvironmentProvider",
    "ContextVarEnvironmentProvider", 
    "StandardEnvironmentProvider",
    "EnvironmentProviderStub",
    "get_default_environment_provider",
    "set_default_environment_provider",
    "get_env",
    "get_all_env",
]
