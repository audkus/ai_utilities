"""Provider capabilities for different AI providers."""

from dataclasses import dataclass
from typing import Optional, Set


@dataclass
class ProviderCapabilities:
    """Defines the capabilities of an AI provider."""
    
    # Core capabilities
    supports_text: bool = True
    supports_json_mode: bool = False
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_images: bool = False
    
    # Model capabilities
    supports_temperature: bool = True
    supports_max_tokens: bool = True
    supports_top_p: bool = False
    supports_frequency_penalty: bool = False
    supports_presence_penalty: bool = False
    
    # Additional metadata
    max_context_length: Optional[int] = None
    supported_models: Optional[Set[str]] = None
    
    @classmethod
    def openai(cls) -> "ProviderCapabilities":
        """Capabilities for OpenAI provider."""
        return cls(
            supports_text=True,
            supports_json_mode=True,
            supports_streaming=True,
            supports_tools=True,
            supports_images=True,
            supports_temperature=True,
            supports_max_tokens=True,
            supports_top_p=True,
            supports_frequency_penalty=True,
            supports_presence_penalty=True,
            max_context_length=128000,  # GPT-4-turbo context
        )
    
    @classmethod
    def openai_compatible(cls) -> "ProviderCapabilities":
        """Capabilities for OpenAI-compatible providers (conservative defaults)."""
        return cls(
            supports_text=True,
            supports_json_mode=True,  # Allow but warn that support varies
            supports_streaming=False,  # Varies by provider, be conservative
            supports_tools=False,      # Varies by provider, be conservative
            supports_images=False,     # Varies by provider, be conservative
            supports_temperature=True,
            supports_max_tokens=True,
            supports_top_p=False,
            supports_frequency_penalty=False,
            supports_presence_penalty=False,
            max_context_length=4096,   # Conservative for local models
        )
