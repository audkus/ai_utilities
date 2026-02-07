"""Provider implementations for AI models."""

from typing import TYPE_CHECKING

from .base_provider import BaseProvider
from .provider_factory import create_provider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import ProviderCapabilityError, ProviderConfigurationError, FileTransferError, MissingOptionalDependencyError

# Re-export modules for direct access
from . import provider_factory as provider_factory
from . import openai_compatible_provider as openai_compatible_provider

# Make OpenAIProvider available lazily
if TYPE_CHECKING:
    from .openai_provider import OpenAIProvider
    from .openai_compatible_provider import OpenAICompatibleProvider
else:
    try:
        from .openai_provider import OpenAIProvider
    except ImportError as e:
        _openai_import_error = e
        class OpenAIProvider:  # callable (class)
            def __init__(self, *args, **kwargs):
                raise MissingOptionalDependencyError(
                    "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
                ) from _openai_import_error

    # OpenAICompatibleProvider is already imported via openai_compatible_provider module above

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
