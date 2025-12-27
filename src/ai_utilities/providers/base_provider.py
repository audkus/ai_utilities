"""Base provider interface for AI models."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Dict, List, Literal, Union


class BaseProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Ask a single question to the AI.
        
        Args:
            prompt: Single prompt string
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response string for text format, dict for json format
        """
        pass
    
    @abstractmethod
    def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, Dict[str, Any]]]:
        """Ask multiple questions to the AI.
        
        Args:
            prompts: Sequence of prompt strings
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of response strings or dicts based on return_format
        """
        pass
    
    def ask_text(self, prompt: str, **kwargs) -> str:
        """Ask a single question and always return text.
        
        This is a convenience method that always requests text format.
        Default implementation calls ask() with return_format="text".
        
        Args:
            prompt: Single prompt string
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response as string
        """
        response = self.ask(prompt, return_format="text", **kwargs)
        if isinstance(response, str):
            return response
        else:
            # Provider returned dict despite asking for text, convert to string
            return str(response)
