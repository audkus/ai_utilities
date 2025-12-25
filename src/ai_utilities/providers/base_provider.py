"""Base provider interface for AI models."""

from abc import ABC, abstractmethod
from typing import List, Union, Sequence, Literal, Dict, Any


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
