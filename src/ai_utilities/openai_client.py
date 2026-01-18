"""
openai_client.py

Pure OpenAI API client with single responsibility for API communication.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import openai
from openai.types.chat import ChatCompletion

# Patchable symbol that tests can target
OpenAI = openai.OpenAI


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
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def create_chat_completion(
        self,
        model: str,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
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
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        # Add any additional parameters
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
