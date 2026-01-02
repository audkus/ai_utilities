"""OpenAI-compatible provider for local AI servers and gateways."""

import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from ..file_models import UploadedFile
from .base_provider import BaseProvider
from .provider_capabilities import ProviderCapabilities
from .provider_exceptions import (
    ProviderCapabilityError,
    ProviderConfigurationError,
    MissingOptionalDependencyError,
)

logger = logging.getLogger(__name__)

# Track which warnings have been shown to avoid repetition
_shown_warnings = set()


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
            
        # Lazy import OpenAI to avoid dependency issues
        try:
            from ..openai_client import OpenAI
        except ImportError as e:
            raise MissingOptionalDependencyError(
                "OpenAI-compatible provider requires extra 'openai'. Install with: pip install ai-utilities[openai]"
            ) from e
            
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
    
    def _warn_once(self, warning_key: str, message: str) -> None:
        """Show a warning only once to avoid repetition.
        
        Args:
            warning_key: Unique key to track this warning
            message: Warning message to display
        """
        global _shown_warnings
        if warning_key not in _shown_warnings:
            # Add a newline to separate from progress indicator
            print(f"\n{message}")
            logger.warning(message)
            _shown_warnings.add(warning_key)

    def _prepare_request_params(self, **kwargs) -> Dict[str, Any]:
        """Backward-compatible alias for request param filtering.

        Args:
            **kwargs: Parameters passed to provider methods.

        Returns:
            Filtered supported parameters.
        """
        return self._filter_parameters(**kwargs)
    
    def _filter_parameters(self, **kwargs) -> Dict[str, Any]:
        """Filter parameters to only include supported ones.
        
        Args:
            **kwargs: All parameters passed to the provider
            
        Returns:
            Dictionary with only supported parameters
        """
        params = {}
        
        # Add supported parameters
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]
        if "model" in kwargs:
            params["model"] = kwargs["model"]
        
        # Log warnings for unsupported parameters (only once each)
        unsupported_params = set(kwargs.keys()) - set(params.keys()) - {"return_format"}
        for param in unsupported_params:
            explanations = {
                "provider": "Provider selection is handled at client level, not API level",
                "base_url": "Base URL is configured during client initialization", 
                "timeout": "Request timeout is set during client initialization",
                "max_tokens": "Token limits depend on the specific model/server capabilities",
                "temperature": "Temperature may not be supported by all models",
                "extra_headers": "Custom headers may not be supported by all servers"
            }
            
            explanation = explanations.get(param, "This parameter is not supported by all OpenAI-compatible servers")
            self._warn_once(
                f"unsupported_param_{param}",
                f"Parameter '{param}' ignored: {explanation}"
            )
        
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
            self._warn_once(
                "json_mode_warning",
                "JSON mode requested but not guaranteed to be supported by this OpenAI-compatible provider"
            )
        
        # Prepare request parameters
        request_params = self._filter_parameters(**kwargs)
        
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
    
    def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: Optional[str] = None, mime_type: Optional[str] = None
    ) -> UploadedFile:
        """Upload a file to the provider.
        
        Args:
            path: Path to the file to upload
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            filename: Optional custom filename (defaults to path.name)
            mime_type: Optional MIME type (auto-detected if None)
            
        Returns:
            UploadedFile with metadata about the uploaded file
            
        Raises:
            ProviderCapabilityError: Always - OpenAI-compatible providers don't support Files API
        """
        raise ProviderCapabilityError(
            "Files API (upload)", 
            "openai_compatible"
        )
    
    def download_file(self, file_id: str) -> bytes:
        """Download file content from the provider.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            File content as bytes
            
        Raises:
            ProviderCapabilityError: Always - OpenAI-compatible providers don't support Files API
        """
        raise ProviderCapabilityError(
            "Files API (download)", 
            "openai_compatible"
        )
    
    def generate_image(
        self, prompt: str, *, size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024", 
        quality: Literal["standard", "hd"] = "standard", n: int = 1
    ) -> List[str]:
        """Generate images using the provider.
        
        Args:
            prompt: Description of the image to generate
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")
            n: Number of images to generate (1-10)
            
        Returns:
            List of image URLs or base64-encoded images
            
        Raises:
            ProviderCapabilityError: Always - OpenAI-compatible providers don't support image generation
        """
        raise ProviderCapabilityError(
            "Image generation", 
            "openai_compatible"
        )
