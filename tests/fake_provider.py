"""Fake provider for testing."""

import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Dict, List, Literal, Union
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities.providers.base_provider import BaseProvider


class FakeProvider(BaseProvider):
    """Fake provider that returns predictable responses for testing."""
    
    def __init__(self, responses: List[str] = None, should_fail: bool = False, 
                 fail_on_call: int = None, delay: float = 0.0):
        """Initialize fake provider with optional predefined responses.
        
        Args:
            responses: List of response templates to cycle through
            should_fail: Whether to raise an exception on all calls
            fail_on_call: Specific call number to fail on (1-based)
            delay: Artificial delay in seconds for testing timeouts
        """
        self.responses = responses or [
            "This is a fake response to: {prompt}",
            "Fake response 2: {prompt}",
            "Fake response 3: {prompt}"
        ]
        self.should_fail = should_fail
        self.fail_on_call = fail_on_call
        self.delay = delay
        self.call_count = 0
        self.last_kwargs = {}  # Track kwargs for testing
        self.last_prompt = None  # Track last prompt for testing
        
    def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Return fake response for single prompt."""
        self._check_for_failure()
        self._simulate_delay()
        
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        return self._get_response(prompt, return_format)
    
    def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, Dict[str, Any]]]:
        """Return fake responses for multiple prompts."""
        self._check_for_failure()
        self._simulate_delay()
        
        self.last_kwargs = kwargs
        return [self._get_response(p, return_format) for p in prompts]
    
    def _check_for_failure(self):
        """Check if this call should fail."""
        self.call_count += 1
        
        if self.should_fail:
            raise FakeProviderError("Simulated provider failure")
        
        if self.fail_on_call and self.call_count >= self.fail_on_call:
            raise FakeProviderError(f"Simulated failure on call {self.call_count}")
    
    def _simulate_delay(self):
        """Simulate network delay if configured."""
        if self.delay > 0:
            import time
            time.sleep(self.delay)
    
    def _get_response(self, prompt: str, return_format: Literal["text", "json"]) -> Union[str, Dict[str, Any]]:
        """Get response for a single prompt."""
        response = self.responses[(self.call_count - 1) % len(self.responses)]
        
        # Check if the raw response is JSON (starts with { or [ after whitespace)
        # If it's JSON, don't format it - return as-is
        stripped = response.strip()
        if stripped.startswith(('{', '[')):
            formatted_response = response  # Don't format JSON responses
        else:
            # Only format text responses that contain {prompt}
            try:
                formatted_response = response.format(prompt=prompt)
            except KeyError:
                # If formatting fails, return as-is
                formatted_response = response
        
        if return_format == "json":
            return {"answer": formatted_response}
        
        return formatted_response
    
    def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: str = None, mime_type: str = None
    ):
        """Fake file upload for testing."""
        from ai_utilities.file_models import UploadedFile
        from datetime import datetime
        
        return UploadedFile(
            file_id=f"fake-file-{self.call_count}",
            filename=filename or path.name,
            bytes=1000,
            provider="fake",
            purpose=purpose,
            created_at=datetime.now()
        )
    
    def download_file(self, file_id: str) -> bytes:
        """Fake file download for testing."""
        return b"Fake file content for testing purposes"
    
    def generate_image(
        self, prompt: str, *, size: str = "1024x1024", quality: str = "standard", n: int = 1
    ) -> List[str]:
        """Fake image generation for testing."""
        return [f"https://fake-image-url.com/{size}/{self.call_count}.png" for _ in range(n)]
    
    def transcribe_audio(self, *args, **kwargs):
        """Fake audio transcription."""
        if self.should_fail or (self.fail_on_call == self.call_count):
            raise FakeProviderError("Fake transcription failed")
        
        # Return a mock result object
        result = Mock()
        result.text = "This is a fake transcription"
        return result
    
    def generate_audio(self, *args, **kwargs):
        """Fake audio generation."""
        if self.should_fail or (self.fail_on_call == self.call_count):
            raise FakeProviderError("Fake audio generation failed")
        return b"fake_audio_data"


class FakeAsyncProvider:
    """Fake async provider for testing AsyncAiClient."""
    
    def __init__(self, responses: List[str] = None, should_fail: bool = False, 
                 fail_on_call: int = None, delay: float = 0.0):
        """Initialize fake async provider."""
        self.sync_provider = FakeProvider(responses, should_fail, fail_on_call, delay)
        self.call_count = 0
        
    async def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Async version of ask."""
        # Simulate async behavior
        await asyncio.sleep(0.001)  # Tiny delay to make it truly async
        return self.sync_provider.ask(prompt, return_format=return_format, **kwargs)
    
    async def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, Dict[str, Any]]]:
        """Async version of ask_many."""
        await asyncio.sleep(0.001)  # Tiny delay to make it truly async
        return self.sync_provider.ask_many(prompts, return_format=return_format, **kwargs)
    
    # Delegate other methods to sync provider
    def upload_file(self, *args, **kwargs):
        return self.sync_provider.upload_file(*args, **kwargs)
    
    def download_file(self, *args, **kwargs):
        return self.sync_provider.download_file(*args, **kwargs)
    
    def generate_image(self, *args, **kwargs):
        return self.sync_provider.generate_image(*args, **kwargs)


class FakeProviderError(Exception):
    """Fake provider error for testing error handling."""
    pass
