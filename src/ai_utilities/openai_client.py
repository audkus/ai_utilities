"""
openai_client.py

Pure OpenAI API client with single responsibility for API communication.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

# OpenAI imports - lazy loaded to avoid import-time dependencies
_openai = None
OpenAI = None

def _get_openai():
    """Lazy import of openai module."""
    global _openai, OpenAI
    if _openai is None:
        try:
            import openai
            _openai = openai
            # Only set OpenAI if it's not already set (e.g., by tests)
            if OpenAI is None:
                OpenAI = openai.OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package is required for OpenAI client. "
                "Install it with: pip install 'ai-utilities[openai]'"
            )
    return _openai


def _create_openai_sdk_client(api_key: str, base_url: Optional[str] = None, timeout: Optional[float] = None):
    """
    Create and return an OpenAI SDK client instance.
    
    This is the single boundary for SDK client creation, making it
    the correct target for test patching.
    
    Args:
        api_key: OpenAI API key
        base_url: Custom base URL (optional)
        timeout: Request timeout in seconds
        
    Returns:
        OpenAI SDK client instance
    """
    openai_mod = _get_openai()
    # Use the global OpenAI if set (e.g., by tests), otherwise get from module
    ctor = OpenAI or getattr(openai_mod, 'OpenAI')
    return ctor(api_key=api_key, base_url=base_url, timeout=timeout)


class OpenAIClient:
    """
    Pure OpenAI API client responsible only for API communication.
    
    This class has a single responsibility: making requests to OpenAI's API.
    It doesn't handle rate limiting, response processing, or configuration.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: Optional[float] = None) -> None:
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key
            base_url: Custom base URL (optional)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.client = _create_openai_sdk_client(api_key=api_key, base_url=base_url, timeout=timeout)

    def create_chat_completion(
        self,
        model: str,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Create a chat completion with OpenAI API.
        
        Args:
            model: OpenAI model name
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            ChatCompletion response from OpenAI API
            
        Raises:
            OpenAI API exceptions for API errors
        """
        _get_openai()  # Ensure openai is imported
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        params.update(kwargs)
        
        return self.client.chat.completions.create(**params)

    def get_models(self):
        """
        Get list of available models from OpenAI API.
        
        Returns:
            List of available models
            
        Raises:
            OpenAI API exceptions for API errors
        """
        return self.client.models.list()
