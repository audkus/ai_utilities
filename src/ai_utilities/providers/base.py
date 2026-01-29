"""Base provider interfaces for sync and async AI clients."""

from typing import Any, Dict, Literal, Protocol, Union, runtime_checkable
from pathlib import Path

from ..file_models import UploadedFile


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

    def upload_file(self, path: Path, *, purpose: str = "assistants", filename: str = None, mime_type: str = None) -> UploadedFile:
        """Upload a file to the AI provider.
        
        Args:
            path: Path to the file to upload
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            filename: Optional custom filename (defaults to path.name)
            mime_type: Optional MIME type (auto-detected if None)
            
        Returns:
            UploadedFile with metadata about the uploaded file
        """
        ...

    def download_file(self, file_id: str) -> bytes:
        """Download file content from the AI provider.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            File content as bytes
        """
        ...

    def list_files(self, *, purpose: str = None) -> list[UploadedFile]:
        """List all uploaded files.
        
        Args:
            purpose: Optional filter by purpose (e.g., "assistants", "fine-tune")
            
        Returns:
            List of UploadedFile objects
        """
        ...

    def delete_file(self, file_id: str) -> bool:
        """Delete a uploaded file.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            True if deletion was successful
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

    async def upload_file(self, path: Path, *, purpose: str = "assistants", filename: str = None, mime_type: str = None) -> UploadedFile:
        """Upload a file to the AI provider asynchronously.
        
        Args:
            path: Path to the file to upload
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            filename: Optional custom filename (defaults to path.name)
            mime_type: Optional MIME type (auto-detected if None)
            
        Returns:
            UploadedFile with metadata about the uploaded file
        """
        ...

    async def download_file(self, file_id: str) -> bytes:
        """Download file content from the AI provider asynchronously.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            File content as bytes
        """
        ...

    async def list_files(self, *, purpose: str = None) -> list[UploadedFile]:
        """List all uploaded files asynchronously.
        
        Args:
            purpose: Optional filter by purpose (e.g., "assistants", "fine-tune")
            
        Returns:
            List of UploadedFile objects
        """
        ...

    async def delete_file(self, file_id: str) -> bool:
        """Delete a uploaded file asynchronously.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            True if deletion was successful
        """
        ...
