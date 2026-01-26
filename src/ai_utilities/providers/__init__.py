"""Provider implementations for AI models."""

from .base_provider import BaseProvider
from .provider_factory import create_provider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import ProviderCapabilityError, ProviderConfigurationError, FileTransferError, MissingOptionalDependencyError

# Re-export modules for direct access
from . import provider_factory as provider_factory
from . import openai_compatible_provider as openai_compatible_provider

# Make OpenAIProvider available lazily
try:
    from .openai_provider import OpenAIProvider as OpenAIProvider
except ImportError as e:
    _openai_import_error = e
    class OpenAIProvider:  # callable (class)
        def __init__(self, *args, **kwargs):
            raise MissingOptionalDependencyError(
                "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
            ) from _openai_import_error

# Make OpenAICompatibleProvider available lazily for patching
try:
    from .openai_compatible_provider import OpenAICompatibleProvider as OpenAICompatibleProvider
except ImportError as e:
    _openai_compatible_import_error = e
    class OpenAICompatibleProvider:  # callable (class)
        def __init__(self, *args, **kwargs):
            raise MissingOptionalDependencyError(
                "OpenAI Compatible provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
            ) from _openai_compatible_import_error

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
