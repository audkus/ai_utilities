"""Fake provider for testing."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Dict, List, Literal, Union

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities.providers.base_provider import BaseProvider


class FakeProvider(BaseProvider):
    """Fake provider that returns predictable responses for testing."""
    
    def __init__(self, responses: List[str] = None):
        """Initialize fake provider with optional predefined responses."""
        self.responses = responses or [
            "This is a fake response to: {prompt}",
            "Fake response 2: {prompt}",
            "Fake response 3: {prompt}"
        ]
        self.call_count = 0
        self.last_kwargs = {}  # Track kwargs for testing
    
    def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Return fake response for single prompt."""
        self.last_kwargs = kwargs
        return self._get_response(prompt, return_format)
    
    def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, Dict[str, Any]]]:
        """Return fake responses for multiple prompts."""
        self.last_kwargs = kwargs
        return [self._get_response(p, return_format) for p in prompts]
    
    def _get_response(self, prompt: str, return_format: Literal["text", "json"]) -> Union[str, Dict[str, Any]]:
        """Get response for a single prompt."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        
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
