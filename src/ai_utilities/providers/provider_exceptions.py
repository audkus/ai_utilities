"""Provider-specific exceptions."""


class ProviderCapabilityError(Exception):
    """Raised when a requested capability is not supported by the provider."""
    
    def __init__(self, capability: str, provider: str):
        self.capability = capability
        self.provider = provider
        super().__init__(f"Provider '{provider}' does not support capability: {capability}")


class ProviderConfigurationError(Exception):
    """Raised when provider configuration is invalid."""
    
    def __init__(self, message: str, provider: str = None):
        self.provider = provider
        if provider:
            super().__init__(f"Provider '{provider}' configuration error: {message}")
        else:
            super().__init__(f"Provider configuration error: {message}")
