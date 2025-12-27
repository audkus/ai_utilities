"""OpenAI-compatible provider for local AI servers and gateways."""

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from openai import OpenAI

from .base_provider import BaseProvider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import ProviderCapabilityError, ProviderConfigurationError

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseProvider):
    """Provider for OpenAI-compatible endpoints (local servers, gateways, etc.)."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Initialize OpenAI-compatible provider.
        
        Args:
            api_key: API key (can be dummy for local servers)
            base_url: Base URL for the OpenAI-compatible endpoint (required)
            timeout: Request timeout in seconds
            extra_headers: Additional headers to send with requests
            **kwargs: Additional initialization parameters
            
        Raises:
            ProviderConfigurationError: If base_url is not provided
        """
        if not base_url:
            raise ProviderConfigurationError(
                "base_url is required for openai_compatible provider",
                "openai_compatible"
            )
        
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.extra_headers = extra_headers or {}
        self.capabilities = ProviderCapabilities.openai_compatible()
        
        # Initialize OpenAI client with custom base_url
        client_kwargs = {
            "api_key": api_key or "dummy-key",  # OpenAI SDK requires API key
            "base_url": self.base_url,
            "timeout": timeout,
        }
        
        # Add extra headers if provided
        if self.extra_headers:
            client_kwargs["default_headers"] = self.extra_headers
            
        self.client = OpenAI(**client_kwargs)
        logger.info(f"Initialized OpenAI-compatible provider with base_url: {self.base_url}")
    
    def _check_capability(self, capability: str) -> None:
        """Check if the provider supports a capability.
        
        Args:
            capability: Name of the capability to check
            
        Raises:
            ProviderCapabilityError: If capability is not supported
        """
        capability_map = {
            "json_mode": self.capabilities.supports_json_mode,
            "streaming": self.capabilities.supports_streaming,
            "tools": self.capabilities.supports_tools,
            "images": self.capabilities.supports_images,
        }
        
        if capability in capability_map and not capability_map[capability]:
            raise ProviderCapabilityError(capability, "openai_compatible")
    
    def _prepare_request_params(self, **kwargs) -> Dict[str, Any]:
        """Prepare request parameters, filtering unsupported ones.
        
        Args:
            **kwargs: Request parameters
            
        Returns:
            Filtered parameters for the provider
        """
        # Start with common parameters that are supported
        params = {}
        
        # Add supported parameters
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]
        if "model" in kwargs:
            params["model"] = kwargs["model"]
        
        # Log warnings for unsupported parameters
        unsupported_params = set(kwargs.keys()) - set(params.keys()) - {"return_format"}
        for param in unsupported_params:
            logger.warning(f"Parameter '{param}' is not supported by openai_compatible provider and will be ignored")
        
        return params
    
    def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Ask a single question to the AI.
        
        Args:
            prompt: Single prompt string
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response string for text format, dict for json format
            
        Raises:
            ProviderCapabilityError: If JSON mode is requested but not supported
        """
        # Check JSON mode capability
        if return_format == "json":
            self._check_capability("json_mode")
            logger.warning("JSON mode requested but not guaranteed to be supported by this OpenAI-compatible provider")
        
        # Prepare request parameters
        request_params = self._prepare_request_params(**kwargs)
        
        try:
            # Make the request
            response = self.client.chat.completions.create(
                model=request_params.get("model", "gpt-3.5-turbo"),  # Default model
                messages=[{"role": "user", "content": prompt}],
                temperature=request_params.get("temperature", 0.7),
                max_tokens=request_params.get("max_tokens"),
                **({} if return_format == "text" else {"response_format": {"type": "json_object"}})
            )
            
            content = response.choices[0].message.content
            
            if return_format == "json" and content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    # Return raw text if JSON parsing fails
                    return content
            else:
                return content
                
        except Exception as e:
            logger.error(f"Error in openai_compatible provider ask: {e}")
            raise
    
    def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, Dict[str, Any]]]:
        """Ask multiple questions to the AI.
        
        Args:
            prompts: Sequence of prompt strings
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of responses
        """
        responses = []
        for prompt in prompts:
            response = self.ask(prompt, return_format=return_format, **kwargs)
            responses.append(response)
        return responses
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get the provider's capabilities."""
        return self._capabilities
    
    @capabilities.setter
    def capabilities(self, value: ProviderCapabilities) -> None:
        """Set the provider's capabilities."""
        self._capabilities = value
