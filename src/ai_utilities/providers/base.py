"""Base provider interfaces for sync and async AI clients."""

from typing import Any, Dict, Literal, Protocol, Union, runtime_checkable


@runtime_checkable
class SyncProvider(Protocol):
    """Protocol for synchronous AI providers."""
    
    def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Ask a synchronous question to the AI provider.
        
        Args:
            prompt: The prompt to send
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response as string or dict
        """
        ...


@runtime_checkable
class AsyncProvider(Protocol):
    """Protocol for asynchronous AI providers."""
    
    async def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Ask an asynchronous question to the AI provider.
        
        Args:
            prompt: The prompt to send
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response as string or dict
        """
        ...
