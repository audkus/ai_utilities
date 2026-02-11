"""Test utilities for provider testing."""

from typing import Any, Dict, List, Literal, Optional, Union
from unittest.mock import MagicMock

from ai_utilities.file_models import UploadedFile
from ai_utilities.providers.base_provider import BaseProvider
from ai_utilities.providers.provider_capabilities import ProviderCapabilities


class DummyProvider(BaseProvider):
    """A minimal provider implementation for testing that never imports optional dependencies."""
    
    def __init__(self, **kwargs: Any):
        """Initialize dummy provider."""
        self.capabilities = ProviderCapabilities.all_enabled()
        self.settings = type('Settings', (), kwargs)()
        
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "dummy"
    
    def _check_capability(self, capability: str) -> None:
        """Dummy provider supports all capabilities."""
        pass
    
    def ask(
        self,
        prompt: str,
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs: Any
    ) -> Union[str, dict, list]:
        """Return deterministic fake response."""
        if return_format == "json":
            return {"response": f"Dummy response to: {prompt}"}
        return f"Dummy response to: {prompt}"
    
    def ask_many(
        self,
        prompts: List[str],
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs: Any
    ) -> List[Union[str, dict, list]]:
        """Return deterministic fake responses for multiple prompts."""
        return [self.ask(prompt, return_format=return_format, **kwargs) for prompt in prompts]
    
    def ask_stream(
        self,
        prompt: str,
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs: Any
    ):
        """Yield deterministic fake streaming response."""
        response = self.ask(prompt, return_format=return_format, **kwargs)
        if isinstance(response, str):
            for char in response:
                yield char
        else:
            yield str(response)
    
    def upload_file(self, file_path: str) -> UploadedFile:
        """Return fake uploaded file."""
        return UploadedFile(
            file_id="dummy-file-id",
            filename=file_path.split("/")[-1] if "/" in file_path else file_path,
            bytes=1024,
            provider="dummy",
            purpose="dummy"
        )
    
    def list_files(self) -> List[UploadedFile]:
        """Return empty file list."""
        return []
    
    def delete_file(self, file_id: str) -> bool:
        """Always return True for dummy provider."""
        return True
    
    def get_file(self, file_id: str) -> Optional[UploadedFile]:
        """Return None for dummy provider."""
        return None


class AsyncDummyProvider:
    """An async dummy provider for testing."""
    
    def __init__(self, **kwargs: Any):
        """Initialize async dummy provider."""
        self.capabilities = ProviderCapabilities.all_enabled()
        self.settings = type('Settings', (), kwargs)()
        
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "async_dummy"
    
    def _check_capability(self, capability: str) -> None:
        """Dummy provider supports all capabilities."""
        pass
    
    async def ask(
        self,
        prompt: str,
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs: Any
    ) -> Union[str, dict, list]:
        """Return deterministic fake async response."""
        if return_format == "json":
            return {"response": f"Async dummy response to: {prompt}"}
        return f"Async dummy response to: {prompt}"
    
    async def ask_many(
        self,
        prompts: List[str],
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs: Any
    ) -> List[Union[str, dict, list]]:
        """Return deterministic fake async responses for multiple prompts."""
        responses = []
        for prompt in prompts:
            response = await self.ask(prompt, return_format=return_format, **kwargs)
            responses.append(response)
        return responses
    
    async def ask_stream(
        self,
        prompt: str,
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs: Any
    ):
        """Yield deterministic fake async streaming response."""
        response = await self.ask(prompt, return_format=return_format, **kwargs)
        if isinstance(response, str):
            for char in response:
                yield char
        else:
            yield str(response)
    
    async def upload_file(self, file_path: str) -> UploadedFile:
        """Return fake uploaded file."""
        return UploadedFile(
            file_id="async-dummy-file-id",
            filename=file_path.split("/")[-1] if "/" in file_path else file_path,
            bytes=1024,
            provider="async_dummy",
            purpose="dummy"
        )
    
    async def list_files(self) -> List[UploadedFile]:
        """Return empty file list."""
        return []
    
    async def delete_file(self, file_id: str) -> bool:
        """Always return True for dummy provider."""
        return True
    
    async def get_file(self, file_id: str) -> Optional[UploadedFile]:
        """Return None for dummy provider."""
        return None
