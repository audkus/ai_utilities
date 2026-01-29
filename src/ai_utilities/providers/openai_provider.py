"""OpenAI provider implementation."""

import json
import mimetypes
import re
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import openai
from openai.types.chat import ChatCompletion

# Patchable symbol for tests
OpenAI = openai.OpenAI

from ..file_models import UploadedFile
from .base_provider import BaseProvider
from .provider_exceptions import FileTransferError


class OpenAIProvider(BaseProvider):
    """OpenAI provider for AI requests."""
    
    def __init__(self, settings, client=None):
        """Initialize OpenAI provider.
        
        Args:
            settings: AI settings containing api_key, model, temperature, etc.
            client: Optional OpenAI client instance (for testing)
        """
        self.settings = settings
        if client is not None:
            self.client = client
        else:
            self.client = OpenAI(
                api_key=settings.api_key,
                base_url=settings.base_url,
                timeout=settings.timeout
            )
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Ask a single question to OpenAI.
        
        Args:
            prompt: Single prompt string
            return_format: Format for response ("text" or "json")
            **kwargs: Additional parameters (model, temperature, etc.)
            
        Returns:
            Response string for text format, dict for json format
        """
        return self._ask_single(prompt, return_format, **kwargs)
    
    def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, Dict[str, Any]]]:
        """Ask multiple questions to OpenAI.
        
        Args:
            prompts: Sequence of prompt strings
            return_format: Format for response ("text" or "json")
            **kwargs: Additional parameters (model, temperature, etc.)
            
        Returns:
            List of response strings or dicts based on return_format
        """
        return [self._ask_single(prompt, return_format, **kwargs) for prompt in prompts]
    
    def _ask_single(self, prompt: str, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Ask a single question to OpenAI."""
        # Merge settings with kwargs, giving priority to kwargs
        params: Dict[str, Any] = {
            "model": kwargs.get("model", self.settings.model),
            "temperature": kwargs.get("temperature", self.settings.temperature),
            "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
        }
        
        # Add response format for JSON mode if requested and model supports it
        model = params["model"]
        
        # JSON mode is supported by recent GPT models and most OpenAI-compatible models
        # Use model name patterns to detect JSON capability
        supports_json_mode = (
            model.startswith("gpt-4") or 
            model.startswith("gpt-3.5-turbo") or
            "json" in model.lower() or
            model.startswith("claude-3") or
            model in ["o1-preview", "o1-mini"] or
            # For OpenAI-compatible providers, assume JSON support unless explicitly disabled
            self.provider_name != "openai"
        )
        
        if return_format == "json" and supports_json_mode:
            params["response_format"] = {"type": "json_object"}
        
        messages = [{"role": "user", "content": prompt}]
        
        response: ChatCompletion = self.client.chat.completions.create(
            messages=messages,
            **params
        )
        
        result = response.choices[0].message.content or ""
        
        # For JSON mode with native support, the result should already be valid JSON
        if return_format == "json" and params.get("response_format"):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If parsing fails, return the raw string wrapped in a dict
                return {"response": result}
        
        # For JSON requests without native support, extract JSON from text
        if return_format == "json":
            return self._extract_json(result)
        
        return result
    
    def _ask_batch(self, prompts: List[str], return_format: Literal["text", "json"] = "text", **kwargs) -> List[str]:
        """Ask multiple questions to OpenAI."""
        results = []
        for prompt in prompts:
            result = self._ask_single(prompt, return_format, **kwargs)
            results.append(result)
        return results
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from response text."""
        # Try to find JSON in the response (non-greedy to get first valid JSON)
        for json_match in re.finditer(r'\{.*?\}', text, re.DOTALL):
            try:
                # Validate it's valid JSON and return as dict
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                continue
        
        # If no valid JSON found, return original text wrapped in a dict
        return {"response": text}
    
    def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: Optional[str] = None, mime_type: Optional[str] = None
    ) -> UploadedFile:
        """Upload a file to OpenAI.
        
        Args:
            path: Path to the file to upload
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            filename: Optional custom filename (defaults to path.name)
            mime_type: Optional MIME type (auto-detected if None)
            
        Returns:
            UploadedFile with metadata about the uploaded file
            
        Raises:
            FileTransferError: If upload fails
        """
        try:
            # Validate input
            if not path.exists():
                raise ValueError(f"File does not exist: {path}")
            if not path.is_file():
                raise ValueError(f"Path is not a file: {path}")
            
            # Determine filename and mime type
            upload_filename = filename or path.name
            upload_mime_type = (
                mime_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            )
            
            # Upload file using OpenAI SDK
            with open(path, "rb") as file:
                response = self.client.files.create(
                    file=(upload_filename, file, upload_mime_type),
                    purpose=purpose
                )
            
            # Convert to our UploadedFile model
            return UploadedFile(
                file_id=response.id,
                filename=response.filename,
                bytes=response.bytes,
                provider="openai",
                purpose=response.purpose,
                created_at=(
                    datetime.fromisoformat(response.created_at.replace("Z", "+00:00"))
                    if isinstance(response.created_at, str) and response.created_at
                    else datetime.fromtimestamp(response.created_at)
                    if isinstance(response.created_at, (int, float)) and response.created_at
                    else None
                )
            )
            
        except (Exception) as e:
            # Don't wrap validation errors - let them propagate
            if isinstance(e, ValueError) and ("File does not exist" in str(e) or "Path is not a file" in str(e)):
                raise
            raise FileTransferError("upload", "openai", e) from e
    
    def download_file(self, file_id: str) -> bytes:
        """Download file content from OpenAI.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            File content as bytes
            
        Raises:
            FileTransferError: If download fails
        """
        try:
            if not file_id:
                raise ValueError("file_id cannot be empty")
            
            # Download file content using OpenAI SDK
            response = self.client.files.content(file_id)
            
            # Return the content as bytes
            return response.content
            
        except (Exception) as e:
            # Don't wrap validation errors - let them propagate
            if isinstance(e, ValueError) and "file_id cannot be empty" in str(e):
                raise
            raise FileTransferError("download", "openai", e) from e

    def list_files(self, *, purpose: Optional[str] = None) -> List[UploadedFile]:
        """List all uploaded files from OpenAI.

        Args:
            purpose: Optional filter by purpose (e.g., "assistants", "fine-tune")

        Returns:
            List of UploadedFile objects

        Raises:
            FileTransferError: If listing fails
        """
        try:
            # List files using OpenAI SDK
            response = self.client.files.list(purpose=purpose)
            
            # Convert to our UploadedFile model
            files = []
            for file_obj in response.data:
                files.append(UploadedFile(
                    file_id=file_obj.id,
                    filename=file_obj.filename,
                    bytes=file_obj.bytes,
                    provider="openai",
                    purpose=file_obj.purpose,
                    created_at=(
                        datetime.fromisoformat(file_obj.created_at.replace("Z", "+00:00"))
                        if isinstance(file_obj.created_at, str) and file_obj.created_at
                        else datetime.fromtimestamp(file_obj.created_at)
                        if isinstance(file_obj.created_at, (int, float)) and file_obj.created_at
                        else None
                    )
                ))
            
            return files
            
        except (Exception) as e:
            raise FileTransferError("list", "openai", e) from e

    def delete_file(self, file_id: str) -> bool:
        """Delete a uploaded file from OpenAI.

        Args:
            file_id: ID of the file to delete

        Returns:
            True if deletion was successful

        Raises:
            ValueError: If file_id is invalid
            FileTransferError: If deletion fails
        """
        try:
            if not file_id:
                raise ValueError("file_id cannot be empty")
            
            # Delete file using OpenAI SDK
            response = self.client.files.delete(file_id)
            
            # OpenAI returns {"deleted": true, "id": "file-123"} on success
            return getattr(response, 'deleted', False)
            
        except (Exception) as e:
            # Don't wrap validation errors - let them propagate
            if isinstance(e, ValueError) and "file_id cannot be empty" in str(e):
                raise
            raise FileTransferError("delete", "openai", e) from e

    def generate_image(
        self, prompt: str, *, size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024", 
        quality: Literal["standard", "hd"] = "standard", n: int = 1
    ) -> List[str]:
        """Generate images using OpenAI's DALL-E.
        
        Args:
            prompt: Description of the image to generate
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")
            n: Number of images to generate (1-10)
            
        Returns:
            List of image URLs
            
        Raises:
            FileTransferError: If image generation fails
        """
        try:
            if not prompt:
                raise ValueError("prompt cannot be empty")
            
            if n < 1 or n > 10:
                raise ValueError("n must be between 1 and 10")
            
            # Generate images using OpenAI SDK
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=n
            )
            
            # Extract URLs from response
            image_urls = [image.url for image in response.data]
            return image_urls
            
        except (Exception) as e:
            # Don't wrap validation errors - let them propagate
            if isinstance(e, ValueError) and ("prompt cannot be empty" in str(e) or "n must be between 1 and 10" in str(e)):
                raise
            raise FileTransferError("image generation", "openai", e) from e
