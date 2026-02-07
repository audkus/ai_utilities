"""Provider implementations for AI models."""

from typing import TYPE_CHECKING

from .base_provider import BaseProvider
from .provider_factory import create_provider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import ProviderCapabilityError, ProviderConfigurationError, FileTransferError, MissingOptionalDependencyError

# Re-export modules for direct access
from . import provider_factory as provider_factory
from . import openai_compatible_provider as openai_compatible_provider

# Lazy import for provider classes to preserve import-safety
def __getattr__(name: str) -> object:
    """Lazy import provider classes only when requested."""
    if name == "OpenAIProvider":
        try:
            from .openai_provider import OpenAIProvider
            return OpenAIProvider
        except ImportError as e:
            _openai_import_error = e
            class OpenAIProvider:  # callable (class)
                def __init__(self, *args, **kwargs):
                    raise MissingOptionalDependencyError(
                        "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                    ) from _openai_import_error
            return OpenAIProvider
    
    elif name == "OpenAICompatibleProvider":
        try:
            from .openai_compatible_provider import OpenAICompatibleProvider
            return OpenAICompatibleProvider
        except ImportError as e:
            _openai_compatible_import_error = e
            class OpenAICompatibleProvider:  # callable (class)
                def __init__(self, *args, **kwargs):
                    raise MissingOptionalDependencyError(
                        "OpenAI Compatible provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                    ) from _openai_compatible_import_error
            return OpenAICompatibleProvider
    
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
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
