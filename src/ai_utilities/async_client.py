"""Async AI client with concurrency and retry logic."""

import asyncio
import secrets
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Callable, List, Literal, Optional, Union

from .client import AiSettings
from .file_models import UploadedFile
from .models import AskResult
from .providers.base import AsyncProvider
from .providers.provider_exceptions import FileTransferError, ProviderCapabilityError


class AsyncOpenAIProvider(AsyncProvider):
    """Async OpenAI provider implementation."""
    
    def __init__(self, settings: AiSettings):
        self.settings = settings
        # Lazy import OpenAIProvider to avoid dependency issues
        from .providers.openai_provider import OpenAIProvider
        self._sync_provider = OpenAIProvider(settings)
    
    async def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, dict, list]:
        """Async ask implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.ask,
            prompt,
            return_format=return_format,
            **kwargs
        )
    
    async def ask_many(self, prompts: Sequence[str], *, return_format: Literal["text", "json"] = "text", **kwargs) -> List[Union[str, dict, list]]:
        """Async ask_many implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.ask_many,
            prompts,
            return_format=return_format,
            **kwargs
        )
    
    async def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: Optional[str] = None, mime_type: Optional[str] = None
    ) -> UploadedFile:
        """Async upload_file implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.upload_file,
            path,
            purpose=purpose,
            filename=filename,
            mime_type=mime_type
        )
    
    async def download_file(self, file_id: str) -> bytes:
        """Async download_file implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.download_file,
            file_id
        )
    
    async def list_files(self, *, purpose: Optional[str] = None) -> List[UploadedFile]:
        """Async list_files implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.list_files,
            purpose=purpose
        )
    
    async def delete_file(self, file_id: str) -> bool:
        """Async delete_file implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.delete_file,
            file_id
        )
    
    async def generate_image(
        self, prompt: str, *, size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024", 
        quality: Literal["standard", "hd"] = "standard", n: int = 1
    ) -> List[str]:
        """Async image generation implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.generate_image,
            prompt, size=size, quality=quality, n=n
        )


class AsyncAiClient:
    """
    Async AI client with concurrency control and retry logic.
    
    This is the asynchronous version of AiClient, designed for high-performance
    applications that need to handle multiple AI requests concurrently. It provides
    the same interface as AiClient but with async/await support.
    
    The async client is ideal for:
    - Web applications handling multiple simultaneous AI requests
    - Batch processing of large numbers of prompts
    - Applications requiring non-blocking AI operations
    
    Example:
        import asyncio
        from ai_utilities import AsyncAiClient
        
        async def main():
            client = AsyncAiClient()
            
            # Single async request
            response = await client.ask("What is the capital of France?")
            
            # Concurrent batch processing
            prompts = ["Q1", "Q2", "Q3", "Q4", "Q5"]
            results = await client.ask_many(prompts, concurrency=3)
            
            # Process results as they complete
            for result in results:
                print(f"Response: {result.response}")
        
        asyncio.run(main())
    
    Features:
        - Async/await support for non-blocking operations
        - Concurrent request processing with configurable limits
        - Retry logic for transient failures
        - Progress callbacks for long-running operations
        - Same interface as synchronous AiClient
        - Usage tracking and progress indication
    """
    
    def __init__(
        self,
        settings: Union[AiSettings, None] = None,
        provider: Union[AsyncProvider, None] = None,
        track_usage: bool = False,
        usage_file: Union[str, None] = None,
        show_progress: bool = True
    ):
        """Initialize async AI client.
        
        Args:
            settings: AI settings containing api_key, model, etc.
            provider: Custom async AI provider (defaults to OpenAI)
            track_usage: Whether to track usage statistics
            usage_file: Custom file for usage tracking
            show_progress: Whether to show progress indicator during requests
        """
        if settings is None:
            settings = AiSettings()
        
        self.settings = settings
        self.provider = provider or AsyncOpenAIProvider(settings)
        self.show_progress = show_progress
    
    async def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, dict, list]:
        """Ask a single question asynchronously.
        
        Args:
            prompt: The prompt to send
            return_format: Format for response ("text" or "json")
            **kwargs: Additional parameters
            
        Returns:
            Response as string or dict
        """
        start_time = time.time()
        
        try:
            response = await self.provider.ask(prompt, return_format=return_format, **kwargs)
            # Calculate duration (currently not used but kept for potential future metrics)
            time.time() - start_time
            return response
        except Exception:
            # Calculate duration even for exceptions (though not currently used)
            time.time() - start_time
            raise
    
    async def ask_many(
        self,
        prompts: Sequence[str],
        *,
        concurrency: int = 5,
        return_format: Literal["text", "json"] = "text",
        fail_fast: bool = False,
        on_progress: Union[Callable[[int, int], None], None] = None,
        **kwargs
    ) -> List[AskResult]:
        """Ask multiple questions asynchronously with concurrency control.
        
        Args:
            prompts: List of prompts to process
            concurrency: Maximum number of concurrent requests
            return_format: Format for responses ("text" or "json")
            fail_fast: If True, cancel remaining requests on first failure
            on_progress: Progress callback (completed, total)
            **kwargs: Additional parameters
            
        Returns:
            List of AskResult objects
        """
        if not prompts:
            return []
        
        semaphore = asyncio.Semaphore(concurrency)
        results = [None] * len(prompts)
        
        # Create tasks directly without inner function to avoid closure issues
        tasks = []
        for i, prompt in enumerate(prompts):
            task = asyncio.create_task(
                self._process_prompt_with_semaphore(
                    i, prompt, semaphore, return_format, on_progress, len(prompts), **kwargs
                )
            )
            tasks.append(task)
        
        try:
            # Wait for all tasks to complete
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results in original order
            for i, completed_task in enumerate(completed_tasks):
                if isinstance(completed_task, Exception):
                    # Handle exception case
                    if isinstance(completed_task, asyncio.CancelledError):
                        results[i] = AskResult(
                            prompt=prompts[i],
                            response=None,
                            error="Canceled",
                            duration_s=0.0,
                            model=self.settings.model,
                            tokens_used=None
                        )
                    else:
                        results[i] = AskResult(
                            prompt=prompts[i],
                            response=None,
                            error=str(completed_task),
                            duration_s=0.0,
                            model=self.settings.model,
                            tokens_used=None
                        )
                else:
                    results[i] = completed_task
                
                # Handle fail_fast
                if fail_fast and results[i] and results[i].error:
                    # Cancel remaining tasks
                    for remaining_task in tasks:
                        if not remaining_task.done():
                            remaining_task.cancel()
                    
                    # Wait for cancellation to complete, ensuring all coroutines are awaited
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Fill remaining results with canceled status
                    for j in range(i + 1, len(prompts)):
                        if results[j] is None:
                            results[j] = AskResult(
                                prompt=prompts[j],
                                response=None,
                                error="Canceled",
                                duration_s=0.0,
                                model=self.settings.model,
                                tokens_used=None
                            )
                    break
        except asyncio.CancelledError:
            # Handle cancellation at the top level
            # Cancel all tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for cancellation to complete, ensuring all coroutines are awaited
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Fill results with canceled status
            for i in range(len(prompts)):
                if results[i] is None:
                    results[i] = AskResult(
                        prompt=prompts[i],
                        response=None,
                        error="Canceled",
                        duration_s=0.0,
                        model=self.settings.model,
                        tokens_used=None
                    )
            
            # Re-raise the cancellation
            raise
        except Exception as e:
            # Cancel all tasks on exception
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for cancellation to complete, ensuring all coroutines are awaited
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Re-raise the exception
            raise
        
        # Fill in any None results (shouldn't happen)
        for i, result in enumerate(results):
            if result is None:
                results[i] = AskResult(
                    prompt=prompts[i],
                    response=None,
                    error="Max retries exceeded",
                    duration_s=0.0,
                    model=self.settings.model,
                    tokens_used=None
                )
        
        return results
    
    async def _process_prompt_with_semaphore(
        self,
        index: int,
        prompt: str,
        semaphore: asyncio.Semaphore,
        return_format: str,
        on_progress: callable,
        total_prompts: int,
        **kwargs
    ) -> AskResult:
        """Process a single prompt with semaphore control."""
        start_time = time.time()
        
        async with semaphore:
            try:
                response = await self.provider.ask(prompt, return_format=return_format, **kwargs)
                duration = time.time() - start_time
                
                result = AskResult(
                    prompt=prompt,
                    response=response,
                    error=None,
                    duration_s=duration,
                    model=self.settings.model,
                    tokens_used=None
                )
                
            except Exception as e:
                duration = time.time() - start_time
                result = AskResult(
                    prompt=prompt,
                    response=None,
                    error=str(e),
                    duration_s=duration,
                    model=self.settings.model,
                    tokens_used=None
                )
            
            # Update progress if callback provided
            if on_progress:
                try:
                    on_progress(index + 1, total_prompts)
                except (TypeError, ValueError, RuntimeError):
                    # Don't let progress callback errors break processing
                    pass
            
            return result
    
    async def ask_many_with_retry(
        self,
        prompts: Sequence[str],
        *,
        concurrency: int = 5,
        return_format: Literal["text", "json"] = "text",
        fail_fast: bool = False,
        on_progress: Union[Callable[[int, int], None], None] = None,
        max_retries: int = 3,
        **kwargs
    ) -> List[AskResult]:
        """Ask multiple questions with retry logic for transient failures.
        
        Args:
            prompts: List of prompts to process
            concurrency: Maximum number of concurrent requests
            return_format: Format for responses ("text" or "json")
            fail_fast: If True, cancel remaining requests on first failure
            on_progress: Progress callback (completed, total)
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters
            
        Returns:
            List of AskResult objects
        """
        if not prompts:
            return []
        
        # Track which prompts need retrying
        remaining_prompts = list(prompts)
        remaining_indices = list(range(len(prompts)))
        results = [None] * len(prompts)
        retry_count = 0
        
        while remaining_prompts and retry_count <= max_retries:
            # Process remaining prompts
            current_results = await self.ask_many(
                remaining_prompts,
                concurrency=concurrency,
                return_format=return_format,
                fail_fast=False,  # Don't fail fast during retries
                on_progress=on_progress,
                **kwargs
            )
            
            # Check for successful results
            new_remaining_prompts = []
            new_remaining_indices = []
            
            for i, (original_index, result) in enumerate(zip(remaining_indices, current_results)):
                if result.error is None:
                    # Success - store result
                    results[original_index] = result
                else:
                    # Check if error is retryable
                    error_msg = result.error.lower()
                    is_retryable = (
                        "rate limit" in error_msg or
                        "timeout" in error_msg or
                        "connection" in error_msg or
                        "temporary" in error_msg or
                        "429" in error_msg or
                        "5" in error_msg  # 5xx errors
                    )
                    
                    if is_retryable and retry_count < max_retries:
                        # Retry this prompt
                        new_remaining_prompts.append(result.prompt)
                        new_remaining_indices.append(original_index)
                    else:
                        # Don't retry - store final error result
                        results[original_index] = result
            
            # Update remaining lists for next retry
            remaining_prompts = new_remaining_prompts
            remaining_indices = new_remaining_indices
            retry_count += 1
            
            # Exponential backoff with jitter before retry
            if remaining_prompts and retry_count <= max_retries:
                base_delay = 2 ** (retry_count - 1)  # 1, 2, 4 seconds
                # Use secrets for cryptographically secure jitter (timing only, not sensitive)
                jitter_range = int(0.1 * base_delay * 1000)  # Convert to milliseconds
                jitter_ms = secrets.randbelow(jitter_range + 1) if jitter_range > 0 else 0
                jitter = jitter_ms / 1000.0  # Convert back to seconds
                await asyncio.sleep(base_delay + jitter)
        
        # Fill in any remaining None results (shouldn't happen)
        for i, result in enumerate(results):
            if result is None:
                results[i] = AskResult(
                    prompt=prompts[i],
                    response=None,
                    error="Max retries exceeded",
                    duration_s=0.0,
                    model=self.settings.model,
                    tokens_used=None
                )
        
        return results
    
    async def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: Optional[str] = None, mime_type: Optional[str] = None
    ) -> UploadedFile:
        """Upload a file to the AI provider asynchronously.
        
        Args:
            path: Path to the file to upload
            purpose: Purpose of the upload (e.g., "assistants", "fine-tune")
            filename: Optional custom filename (defaults to path.name)
            mime_type: Optional MIME type (auto-detected if None)
            
        Returns:
            UploadedFile with metadata about the uploaded file
            
        Raises:
            ValueError: If file path is invalid
            FileTransferError: If upload fails
            ProviderCapabilityError: If provider doesn't support file uploads
            
        Example:
            >>> file = await client.upload_file("document.pdf", purpose="assistants")
            >>> print(f"Uploaded: {file.file_id}")
        """
        # Validate input
        if not isinstance(path, Path):
            path = Path(path)
        
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        # Delegate to async provider
        try:
            return await self.provider.upload_file(path, purpose=purpose, filename=filename, mime_type=mime_type)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("upload", self.provider.__class__.__name__, e) from e
    
    async def download_file(self, file_id: str, *, to_path: Optional[Path] = None) -> Union[bytes, Path]:
        """Download file content from the AI provider asynchronously.
        
        Args:
            file_id: ID of the file to download
            to_path: Optional path to save the file (returns bytes if None)
            
        Returns:
            File content as bytes if to_path is None, or Path to saved file
            
        Raises:
            ValueError: If file_id is invalid
            FileTransferError: If download fails
            ProviderCapabilityError: If provider doesn't support file downloads
            
        Example:
            >>> # Download as bytes
            >>> content = await client.download_file("file-123")
            >>> 
            >>> # Download to file
            >>> path = await client.download_file("file-123", to_path="downloaded.pdf")
        """
        if not file_id:
            raise ValueError("file_id cannot be empty")
        
        # Delegate to async provider
        try:
            content = await self.provider.download_file(file_id)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("download", self.provider.__class__.__name__, e) from e
        
        # Handle saving to file if requested
        if to_path is not None:
            if not isinstance(to_path, Path):
                to_path = Path(to_path)
            
            # Create parent directories if needed
            to_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(to_path, "wb") as f:
                f.write(content)
            
            return to_path
        
        # Return raw bytes
        return content

    async def list_files(self, *, purpose: Optional[str] = None) -> List[UploadedFile]:
        """List all uploaded files asynchronously.

        Args:
            purpose: Optional filter by purpose (e.g., "assistants", "fine-tune")

        Returns:
            List of UploadedFile objects

        Raises:
            ProviderCapabilityError: If provider doesn't support file listing
            FileTransferError: If listing fails

        Example:
            >>> files = await client.list_files()
            >>> assistants_files = await client.list_files(purpose="assistants")
        """
        # Delegate to async provider
        try:
            return await self.provider.list_files(purpose=purpose)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("list", self.provider.__class__.__name__, e) from e

    async def delete_file(self, file_id: str) -> bool:
        """Delete a uploaded file asynchronously.

        Args:
            file_id: ID of the file to delete

        Returns:
            True if deletion was successful

        Raises:
            ValueError: If file_id is invalid
            ProviderCapabilityError: If provider doesn't support file deletion
            FileTransferError: If deletion fails

        Example:
            >>> success = await client.delete_file("file-123")
            >>> if success:
            ...     print("File deleted successfully")
        """
        if not file_id:
            raise ValueError("file_id cannot be empty")

        # Delegate to async provider
        try:
            return await self.provider.delete_file(file_id)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("delete", self.provider.__class__.__name__, e) from e

    async def generate_image(
        self, prompt: str, *, size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024", 
        quality: Literal["standard", "hd"] = "standard", n: int = 1
    ) -> List[str]:
        """Generate images using AI asynchronously.
        
        Args:
            prompt: Description of the image to generate
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")
            n: Number of images to generate (1-10)
            
        Returns:
            List of image URLs
            
        Raises:
            ValueError: If prompt is invalid
            FileTransferError: If image generation fails
            ProviderCapabilityError: If provider doesn't support image generation
            
        Example:
            >>> # Generate a single image
            >>> urls = await client.generate_image("A cute dog playing fetch")
            >>> 
            >>> # Generate multiple high-quality images
            >>> urls = await client.generate_image(
            ...     "A majestic lion in the savanna", 
            ...     size="1792x1024", 
            ...     quality="hd", 
            ...     n=3
            ... )
        """
        if not prompt:
            raise ValueError("prompt cannot be empty")
        
        if n < 1 or n > 10:
            raise ValueError("n must be between 1 and 10")
        
        # Delegate to async provider
        try:
            return await self.provider.generate_image(prompt, size=size, quality=quality, n=n)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError("image generation", self.provider.__class__.__name__, e) from e
