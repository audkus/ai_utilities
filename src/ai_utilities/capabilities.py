"""Capability matrix for multi-modal AI provider support.

This module defines the capability matrix that indicates what features
are supported by each provider configuration, future-proofing for
multi-modal functionality.
"""

from typing import Optional
from pydantic import BaseModel


class AiCapabilities(BaseModel):
    """Defines the capabilities supported by an AI provider configuration.
    
    This represents what THIS LIBRARY supports with the given provider,
    not necessarily what the provider itself supports. Capabilities are
    conservative - they return False until the library has stable APIs
    for those features.
    """
    
    text: bool = True
    """Text generation and chat capabilities."""
    
    vision: bool = False
    """Image analysis and vision capabilities."""
    
    audio: bool = False
    """Audio transcription and generation capabilities."""
    
    files: bool = False
    """File upload and processing capabilities."""
    
    embeddings: bool = False
    """Text embedding and vector search capabilities."""
    
    tools: bool = False
    """Tool calling and plugin capabilities."""
    
    def __repr__(self) -> str:
        """String representation showing enabled capabilities."""
        enabled = [name for name, value in self.model_dump().items() if value]
        return f"AiCapabilities({', '.join(enabled)})"
