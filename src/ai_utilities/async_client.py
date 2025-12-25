"""Async AI client with concurrency and retry logic."""

import asyncio
import random
import time
from typing import Any, Callable, Dict, List, Literal, Sequence, Union

from .client import AiSettings
from .models import AskResult
from .providers.base import AsyncProvider
from .providers.openai_provider import OpenAIProvider


class AsyncOpenAIProvider(AsyncProvider):
    """Async OpenAI provider implementation."""
    
    def __init__(self, settings: AiSettings):
        self.settings = settings
        self._sync_provider = OpenAIProvider(settings)
    
    async def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
        """Async ask implementation using asyncio.to_thread."""
        return await asyncio.to_thread(
            self._sync_provider.ask,
            prompt,
            return_format=return_format,
            **kwargs
        )


class AsyncAiClient:
    """Async AI client with concurrency control and retry logic."""
    
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
    
    async def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, Dict[str, Any]]:
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
            duration = time.time() - start_time
            return response
        except Exception as e:
            duration = time.time() - start_time
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
        completed_count = 0
        first_error = None
        
        async def process_prompt(index: int, prompt: str) -> AskResult:
            nonlocal completed_count, first_error
            
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
                        tokens_used=None  # Would need provider support
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
                    
                    if first_error is None:
                        first_error = e
                
                # Update progress
                completed_count += 1
                if on_progress:
                    try:
                        on_progress(completed_count, len(prompts))
                    except Exception:
                        pass  # Don't let progress callback errors break processing
                
                return result
        
        # Create tasks for all prompts
        tasks = [
            asyncio.create_task(process_prompt(i, prompt))
            for i, prompt in enumerate(prompts)
        ]
        
        try:
            # Wait for all tasks to complete
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results in original order
            for i, completed_task in enumerate(completed_tasks):
                if isinstance(completed_task, Exception):
                    # Handle exception case
                    results[i] = AskResult(
                        prompt=prompts[i],
                        response=None,
                        error=str(completed_task),
                        duration_s=0.0,
                        model=self.settings.model,
                        tokens_used=None
                    )
                else:
                    # Normal result case
                    results[i] = completed_task
                
                # Fail fast if requested and we have an error
                if fail_fast and results[i].error is not None:
                    break
                    
        except Exception:
            # Cancel all remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
        
        # Fill in any None results (canceled tasks)
        for i, result in enumerate(results):
            if result is None:
                results[i] = AskResult(
                    prompt=prompts[i],
                    response=None,
                    error="Canceled",
                    duration_s=0.0,
                    model=self.settings.model,
                    tokens_used=None
                )
        
        return results
    
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
                jitter = random.uniform(0, 0.1 * base_delay)
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
