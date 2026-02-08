"""Provider implementations for AI models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base_provider import BaseProvider
from .provider_factory import create_provider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import ProviderCapabilityError, ProviderConfigurationError, FileTransferError, MissingOptionalDependencyError

# Re-export modules for direct access
from . import provider_factory as provider_factory
from . import openai_compatible_provider as openai_compatible_provider

# TYPE_CHECKING imports for mypy only - no runtime binding
if TYPE_CHECKING:
    from .openai_provider import OpenAIProvider
    from .openai_compatible_provider import OpenAICompatibleProvider

# Lazy import for provider classes to preserve import-safety
def __getattr__(name: str) -> Any:
    """Lazy import provider classes only when requested."""
    # Handle module-level attribute access
    if name in ("openai_provider", "openai_compatible_provider", "base_provider"):
        import importlib
        try:
            return importlib.import_module(f".{name}", __name__)
        except ImportError as e:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'") from e
    
    # Handle class-level attribute access
    if name == "OpenAIProvider":
        try:
            from .openai_provider import OpenAIProvider
            return OpenAIProvider
        except ImportError as e:
            _openai_import_error = e
            class _MissingOpenAIProvider:  # unique name to avoid redef
                def __init__(self, *args, **kwargs):
                    raise MissingOptionalDependencyError(
                        "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                    ) from _openai_import_error
            return _MissingOpenAIProvider
    
    elif name == "OpenAICompatibleProvider":
        try:
            from .openai_compatible_provider import OpenAICompatibleProvider
            return OpenAICompatibleProvider
        except ImportError as e:
            _openai_compatible_import_error = e
            class _MissingOpenAICompatibleProvider:  # unique name to avoid redef
                def __init__(self, *args, **kwargs):
                    raise MissingOptionalDependencyError(
                        "OpenAI Compatible provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                    ) from _openai_compatible_import_error
            return _MissingOpenAICompatibleProvider
    
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__() -> list[str]:
    """Return list of available attributes for dir() completion."""
    return sorted(__all__)

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
