"""Provider implementations for AI models."""

from .base_provider import BaseProvider
from .openai_compatible_provider import OpenAICompatibleProvider
from .provider_factory import create_provider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import ProviderCapabilityError, ProviderConfigurationError, FileTransferError, MissingOptionalDependencyError

# Lazy import OpenAIProvider to avoid dependency issues
def _get_openai_provider():
    try:
        from .openai_provider import OpenAIProvider
        return OpenAIProvider
    except ImportError as e:
        raise MissingOptionalDependencyError(
            "OpenAI provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
        ) from e

# Make OpenAIProvider available lazily
class LazyOpenAIProvider:
    def __getattr__(self, name):
        OpenAIProvider = _get_openai_provider()
        return getattr(OpenAIProvider, name)

OpenAIProvider = LazyOpenAIProvider()

__all__ = [
    "BaseProvider", 
    "OpenAIProvider", 
    "OpenAICompatibleProvider",
    "create_provider",
    "ProviderCapabilities",
    "ProviderCapabilityError", 
    "ProviderConfigurationError",
    "FileTransferError",
    "MissingOptionalDependencyError"
]
