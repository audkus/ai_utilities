"""Base provider interface for AI models."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any, List, Literal, Optional, Sequence, Union

from ..file_models import UploadedFile


class BaseProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def ask(
        self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs
    ) -> Union[str, dict[str, Any]]:
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
    def ask_many(
        self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs
    ) -> list[Union[str, dict[str, Any]]]:
        """Ask multiple questions to the AI.
        
        Args:
            prompts: Sequence of prompt strings
            return_format: Format for response ("text" or "json")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of response strings or dicts based on return_format
        """
        pass
    
    @abstractmethod
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
            FileTransferError: If upload fails
            ProviderCapabilityError: If provider doesn't support file uploads
        """
        pass
    
    @abstractmethod
    def download_file(self, file_id: str) -> bytes:
        """Download file content from the provider.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            File content as bytes
            
        Raises:
            FileTransferError: If download fails
            ProviderCapabilityError: If provider doesn't support file downloads
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
    
    @abstractmethod
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
            FileTransferError: If image generation fails
            ProviderCapabilityError: If provider doesn't support image generation
        """
        pass
