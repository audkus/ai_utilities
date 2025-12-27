"""
openai_client.py

Pure OpenAI API client with single responsibility for API communication.
"""

import logging
from typing import Any, Dict, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Pure OpenAI API client responsible only for API communication.
    
    This class has a single responsibility: making requests to OpenAI's API.
    It doesn't handle rate limiting, response processing, or configuration.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 30):
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
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        logger.debug("OpenAIClient initialized")

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
        logger.debug(f"Creating chat completion with model: {model}")
        
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        # Add any additional parameters
        params.update(kwargs)
        
        response = self.client.chat.completions.create(**params)
        logger.debug("Chat completion created successfully")
        
        return response

    def get_models(self):
        """
        Get list of available models from OpenAI API.
        
        Returns:
            List of available models
            
        Raises:
            OpenAI API exceptions for API errors
        """
        logger.debug("Fetching available models")
        return self.client.models.list()
