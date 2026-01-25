"""
AI Client for v1 API surface.

This module provides the main AiClient class for explicit configuration
without import-time side effects.
"""

import os
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, Optional, TypeVar, Union

# OpenAI imports for embeddings functionality - patchable symbols for tests
import openai
from pydantic import BaseModel

OpenAI = openai.OpenAI

from pydantic import ValidationError

from .cache import CacheBackend, MemoryCache, NullCache, SqliteCache, stable_hash
from .config_models import AiSettings
from .file_models import UploadedFile
from .json_parsing import JsonParseError, create_repair_prompt, parse_json_from_text
from .models import AskResult
from .progress_indicator import ProgressIndicator
from .providers.base_provider import BaseProvider
from .providers.provider_exceptions import FileTransferError, ProviderCapabilityError
from .usage_tracker import UsageScope, UsageStats, create_usage_tracker

# Generic type for typed responses
T = TypeVar("T", bound=BaseModel)


def _sanitize_namespace(ns: str) -> str:
    """Sanitize namespace string to be safe for database use.

    Args:
        ns: Raw namespace string

    Returns:
        Sanitized namespace string
    """
    # Strip whitespace and convert to lowercase
    sanitized = ns.strip().lower()

    # Transliterate unicode to ascii (ñ → n) first
    import re
    import unicodedata

    # Normalize unicode and remove diacritics
    sanitized = unicodedata.normalize("NFKD", sanitized)
    sanitized = "".join(c for c in sanitized if not unicodedata.combining(c))

    # Replace any remaining non-alphanumeric chars (except allowed ones) with underscore
    sanitized = re.sub(r"[^a-z0-9_.-]", "_", sanitized)

    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Limit length and strip leading/trailing underscores
    sanitized = sanitized[:50].strip("_")

    # Return default if empty or only underscores
    if not sanitized or sanitized == "_":
        sanitized = "default"

    return sanitized


def _default_namespace(path: Optional[Path] = None) -> str:
    """Generate default namespace based on current working directory.

    Args:
        path: Optional custom path to use for namespace generation

    Returns:
        Stable namespace string for current project
    """
    # Use provided path or current working directory for namespace
    if path is None:
        path = Path.cwd().resolve()
    cwd_hash = stable_hash({"cwd": str(path)})
    return f"proj_{cwd_hash[:12]}"


def _running_under_pytest() -> bool:
    """Check if we're running under pytest (including collection/import)."""
    return "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules


class AiClient:
    """
    Main AI client for making requests to AI models.

    This is the primary interface for interacting with AI models. It provides
    a simple, clean API for both single and batch requests with support for
    different response formats, usage tracking, and progress indication.

    The client follows a provider architecture, defaulting to OpenAI but
    supporting custom providers through the BaseProvider interface.

    Example:
        # Using environment variables
        client = AiClient()
        response = client.ask("What is the capital of France?")

        # Using explicit settings
        settings = AiSettings(api_key="your-key", model="gpt-4")
        client = AiClient(settings)

        # Batch requests
        prompts = ["Q1", "Q2", "Q3"]
        results = client.ask_many(prompts)

        # JSON responses
        data = client.ask_json("List 5 AI trends as JSON")

    Features:
        - Single and batch AI requests
        - Text and JSON response formats
        - Optional usage tracking
        - Progress indication
        - Provider abstraction
        - Environment-based configuration
        - Non-blocking by default (use CLI for setup)
    """

    def __init__(
        self,
        settings: Optional["AiSettings"] = None,
        provider: Optional[BaseProvider] = None,
        track_usage: bool = False,
        usage_file: Optional[Path] = None,
        show_progress: bool = True,
        cache: Optional[CacheBackend] = None,
    ):
        """Initialize AI client with explicit settings.

        Args:
            settings: AI settings containing api_key, model, temperature, etc.
            provider: Custom AI provider (defaults to OpenAI)
            track_usage: Whether to track usage statistics
            usage_file: Custom file for usage tracking
            show_progress: Whether to show progress indicator during requests
            cache: Optional cache backend to override settings-based cache configuration

        Note:
            The interactive setup has been moved to the CLI. Use 'ai-utilities setup'
            command for interactive configuration. By default, the client only loads
            from .env files.
        """
        if settings is None:
            # Load from .env if it exists, otherwise use empty settings
            if Path(".env").exists():
                settings = AiSettings.from_dotenv(".env")
            else:
                settings = AiSettings()

        self.settings = settings

        # Create provider using factory
        from .providers.provider_factory import create_provider

        self.provider = create_provider(settings, provider)

        # Initialize thread-safe usage tracker with configurable scope
        if track_usage:
            scope = UsageScope(settings.usage_scope)
            self.usage_tracker = create_usage_tracker(
                scope=scope, stats_file=usage_file, client_id=settings.usage_client_id
            )
        else:
            self.usage_tracker = None

        # Initialize cache backend
        if cache is not None:
            # Explicit cache backend takes precedence
            self.cache = cache
        elif not settings.cache_enabled:
            # Caching disabled
            self.cache = NullCache()
        elif settings.cache_backend == "memory":
            # Use memory cache with configured TTL
            self.cache = MemoryCache(default_ttl_s=settings.cache_ttl_s)
        elif settings.cache_backend == "sqlite":
            # SQLite cache with isolation rules for pytest
            if _running_under_pytest() and settings.cache_sqlite_path is None:
                # Strict isolation: disable SQLite cache in pytest unless explicit path
                self.cache = NullCache()
            else:
                # Determine database path
                if settings.cache_sqlite_path is not None:
                    db_path = settings.cache_sqlite_path
                else:
                    # Default to user home directory
                    db_path = Path.home() / ".ai_utilities" / "cache.sqlite"

                # Determine namespace
                if settings.cache_namespace is not None:
                    namespace = _sanitize_namespace(settings.cache_namespace)
                else:
                    # Use pytest namespace when under pytest, otherwise default
                    if _running_under_pytest():
                        namespace = "pytest"
                    else:
                        namespace = _default_namespace()

                # Create SQLite cache
                self.cache = SqliteCache(
                    db_path=db_path,
                    table=settings.cache_sqlite_table,
                    namespace=namespace,
                    wal=settings.cache_sqlite_wal,
                    busy_timeout_ms=settings.cache_sqlite_busy_timeout_ms,
                    default_ttl_s=settings.cache_ttl_s,
                    max_entries=settings.cache_sqlite_max_entries,
                    prune_batch=settings.cache_sqlite_prune_batch,
                )
        else:
            # Default to null cache
            self.cache = NullCache()

        self.show_progress = show_progress

    def _should_use_cache(self, request_params: dict[str, Any]) -> bool:
        """Check if caching should be used for this request.

        Args:
            request_params: Request parameters dictionary

        Returns:
            True if caching should be used
        """
        if not self.settings.cache_enabled:
            return False

        # Don't cache if temperature is too high (non-deterministic)
        temperature = request_params.get("temperature", self.settings.temperature)
        cache_max_temperature = self.settings.cache_max_temperature

        # Add robust numeric coercion for test compatibility
        try:
            temperature_val = float(temperature)
            cache_max_val = float(cache_max_temperature)
            return temperature_val <= cache_max_val
        except (TypeError, ValueError):
            # If coercion fails, don't cache
            return False

    def _build_cache_key(
        self,
        operation: str,
        *,
        prompt: str,
        request_params: dict[str, Any],
        return_format: str,
        extra: Optional[dict[str, Any]] = None,
    ) -> str:
        """Build cache key for request.

        Args:
            operation: Operation type ("ask", "ask_json", "embeddings")
            prompt: Input prompt
            request_params: Request parameters
            return_format: Return format ("text", "json")
            extra: Additional operation-specific data

        Returns:
            Cache key string
        """
        from .cache import normalize_prompt, stable_hash

        # Build key data
        key_data = {
            "operation": operation,
            "provider": self.provider.__class__.__name__,
            "provider_name": getattr(self.settings, "provider", "unknown"),
            "model": request_params.get("model", self.settings.model),
            "return_format": return_format,
            "prompt": normalize_prompt(prompt),
        }

        # Add relevant parameters that affect output
        relevant_params = {}
        if "temperature" in request_params:
            relevant_params["temperature"] = request_params["temperature"]
        if "max_tokens" in request_params:
            relevant_params["max_tokens"] = request_params["max_tokens"]
        if "top_p" in request_params:
            relevant_params["top_p"] = request_params["top_p"]
        if "frequency_penalty" in request_params:
            relevant_params["frequency_penalty"] = request_params["frequency_penalty"]
        if "presence_penalty" in request_params:
            relevant_params["presence_penalty"] = request_params["presence_penalty"]

        if relevant_params:
            key_data["params"] = relevant_params

        # Add operation-specific data
        if extra:
            key_data.update(extra)

        return stable_hash(key_data)

    def check_for_updates(self, force_check: bool = False) -> dict[str, Any]:
        """Manually check for OpenAI model updates with detailed information.

        Args:
            force_check: Force check even if recently checked

        Returns:
            Dictionary with detailed update information
        """
        if not self.settings.api_key:
            print("WARNING: Cannot check for updates: API key not configured")
            return {"error": "API key not configured"}

        print("=== Checking for OpenAI Updates ===")

        # Use force_check to bypass caching
        if force_check:
            return AiSettings.check_for_updates(
                self.settings.api_key, check_interval_days=0
            )
        else:
            return AiSettings.check_for_updates(
                self.settings.api_key, self.settings.update_check_days
            )

    def reconfigure(self) -> None:
        """Manually trigger reconfiguration of settings."""
        print("=== Reconfiguring AI Settings ===")
        self.settings = AiSettings.interactive_setup(force_reconfigure=True)
        from .providers.openai_provider import OpenAIProvider

        self.provider = OpenAIProvider(self.settings)

    def ask(
        self,
        prompt: Union[str, list[str]],
        *,
        return_format: Literal["text", "json"] = "text",
        **kwargs,
    ) -> Union[str, list[str]]:
        """
        Ask a question or multiple questions to the AI.

        This is the primary method for making AI requests. It supports both single
        prompts and batch prompts, with options for text or JSON response formats.

        Args:
            prompt: Single prompt string or list of prompts. If a list is provided,
                   returns a list of responses in the same order.
            return_format: Format for response:
                          - "text": Returns plain text responses (default)
                          - "json": Returns parsed JSON as dict/list
            **kwargs: Additional parameters to override settings:
                     - model: Override the default model
                     - temperature: Override response temperature
                     - max_tokens: Override maximum response tokens
                     - timeout: Override request timeout

        Returns:
            Union[str, list[str], dict, list]: Response in requested format.
                                              Single prompt returns single response,
                                              list of prompts returns list of responses.

        Example:
            client = AiClient()

            # Single question
            answer = client.ask("What is the capital of France?")

            # JSON response
            data = client.ask("List 5 colors", return_format="json")

            # Multiple questions
            questions = ["Q1", "Q2", "Q3"]
            answers = client.ask(questions)

            # With custom parameters
            response = client.ask("Explain AI", temperature=0.3, model="gpt-4")
        """
        # Merge kwargs with settings, excluding internal fields
        request_params = self.settings.model_dump(
            exclude_none=True,
            exclude={
                "api_key",  # Providers already have this from initialization
                "openai_api_key",  # Alias for api_key
                "provider",  # Not a per-request param
                "base_url",  # Not a per-request param
                "timeout",  # Provider init config, not a per-request param
                "request_timeout_s",  # Provider init config, not a per-request param
                "extra_headers",  # Provider init config, not a per-request param
                "usage_scope",  # Internal usage tracking field
                "usage_client_id",  # Internal usage tracking field
                "update_check_days",  # Internal configuration field
                # Knowledge-related settings (not supported by OpenAI API)
                "knowledge_enabled",
                "knowledge_db_path",
                "knowledge_roots",
                "knowledge_chunk_size",
                "knowledge_chunk_overlap",
                "knowledge_min_chunk_size",
                "knowledge_max_file_size",
                "knowledge_use_sqlite_extension",
                "embedding_model",
                # Cache settings, not provider params
                "cache_enabled",
                "cache_backend",
                "cache_ttl_s",
                "cache_max_temperature",
                "cache_sqlite_path",
                "cache_sqlite_table",
                "cache_sqlite_wal",
                "cache_sqlite_busy_timeout_ms",
                "cache_sqlite_max_entries",
                "cache_sqlite_prune_batch",
                "cache_namespace",
            },
        )
        request_params.update(kwargs)

        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)

        with progress:
            if isinstance(prompt, list):
                # Phase 1: Don't cache list prompts
                response = self.provider.ask_many(
                    prompt, return_format=return_format, **request_params
                )
            else:
                # Check cache for single prompt
                cache_key = None
                if self._should_use_cache(request_params):
                    cache_key = self._build_cache_key(
                        "ask",
                        prompt=prompt,
                        request_params=request_params,
                        return_format=return_format,
                    )
                    cached_response = self.cache.get(cache_key)
                    if cached_response is not None:
                        # Track usage for cached responses too
                        if self.usage_tracker:
                            estimated_tokens = len(str(cached_response)) // 4
                            self.usage_tracker.record_usage(estimated_tokens)
                        return cached_response

                # Make actual provider call
                response = self.provider.ask(
                    prompt, return_format=return_format, **request_params
                )

                # Cache successful response
                if cache_key is not None:
                    self.cache.set(cache_key, response, ttl_s=self.settings.cache_ttl_s)

        # Track usage if enabled (basic estimation - provider could return
        # actual counts)
        if self.usage_tracker:
            # This is a rough estimate - actual token counting would need
            # provider support
            estimated_tokens = len(str(response)) // 4  # Rough estimate
            self.usage_tracker.record_usage(estimated_tokens)

        return response

    def get_usage_stats(self) -> Optional[UsageStats]:
        """Get current usage statistics if tracking is enabled.

        Returns:
            UsageStats object if tracking enabled, None otherwise
        """
        if self.usage_tracker:
            return self.usage_tracker.get_stats()
        return None

    def print_usage_summary(self) -> None:
        """Print usage summary if tracking is enabled."""
        if self.usage_tracker:
            self.usage_tracker.print_summary()
        else:
            print("Usage tracking is not enabled.")

    def ask_many(
        self,
        prompts: Sequence[str],
        *,
        return_format: Literal["text", "json"] = "text",
        concurrency: int = 1,
        fail_fast: bool = False,
        **kwargs,
    ) -> list[AskResult]:
        """
        Ask multiple questions with optional concurrency control.

        Processes multiple prompts efficiently with support for concurrent execution
        and detailed result information including timing and error handling.

        Args:
            prompts: List of prompts to process
            return_format: Format for responses:
                          - "text": Returns plain text responses (default)
                          - "json": Returns parsed JSON as dict/list
            concurrency: Number of concurrent requests (must be >= 1).
                        Higher values can improve performance but use more API quota.
            fail_fast: If True, stops processing after first failure.
                      If False, continues processing all prompts.
            **kwargs: Additional parameters to override settings for all requests

        Returns:
            list[AskResult]: List of results containing:
                           - response: The AI response (or None if error)
                           - error: Error message if request failed (or None)
                           - duration_s: Request duration in seconds
                           - prompt: Original prompt (for reference)

        Example:
            client = AiClient()

            # Sequential processing
            prompts = ["What is 2+2?", "What is 3+3?", "What is 4+4?"]
            results = client.ask_many(prompts)

            # Concurrent processing (faster for many requests)
            results = client.ask_many(prompts, concurrency=3)

            # Process results
            for result in results:
                if result.error:
                    print(f"Error: {result.error}")
                else:
                    print(f"Answer: {result.response}")
                    print(f" took {result.duration_s:.2f}s")

            # Fail fast on first error
            results = client.ask_many(prompts, fail_fast=True)
        """
        from .models import AskResult

        # Validate concurrency
        if concurrency <= 0:
            raise ValueError("concurrency must be >= 1")

        results = []

        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)

        with progress:
            for i, prompt in enumerate(prompts):
                start_time = time.time()

                try:
                    # Merge kwargs with settings, excluding internal fields
                    # (same as ask method)
                    request_params = self.settings.model_dump(
                        exclude_none=True,
                        exclude={
                            "api_key",  # Providers already have this from
                            # initialization
                            "usage_scope",  # Internal usage tracking field
                            "usage_client_id",  # Internal usage tracking field
                            "update_check_days",  # Internal configuration field
                            "cache_enabled",  # Cache settings, not provider params
                            "cache_backend",  # Cache settings, not
                            # provider params
                            "cache_ttl_s",  # Cache settings, not provider params
                            "cache_max_temperature",  # Cache settings, not
                            # provider params
                            "cache_sqlite_path",  # Cache settings, not provider params
                            "cache_sqlite_table",  # Cache settings, not provider params
                            "cache_sqlite_wal",  # Cache settings, not provider params
                            "cache_sqlite_busy_timeout_ms",  # Cache settings,
                            # not provider params
                            "cache_sqlite_max_entries",  # Cache settings,
                            # not provider params
                            "cache_sqlite_prune_batch",  # Cache settings,
                            # not provider params
                            "cache_namespace",  # Cache settings, not provider params
                        },
                    )
                    request_params.update(kwargs)

                    response = self.provider.ask(
                        prompt, return_format=return_format, **request_params
                    )
                    duration = time.time() - start_time

                    result = AskResult(
                        prompt=prompt,
                        response=response,
                        error=None,
                        duration_s=duration,
                        model=self.settings.model,
                        tokens_used=None,  # Would need provider support
                    )

                    results.append(result)

                except Exception as e:
                    duration = time.time() - start_time

                    result = AskResult(
                        prompt=prompt,
                        response=None,
                        error=str(e),
                        duration_s=duration,
                        model=self.settings.model,
                        tokens_used=None,
                    )

                    results.append(result)  # Add the failed result first

                    # If fail_fast is enabled, mark remaining prompts as failed
                    if fail_fast:
                        # Mark remaining prompts as cancelled/failed
                        for remaining_prompt in prompts[i + 1 :]:
                            cancelled_result = AskResult(
                                prompt=remaining_prompt,
                                response=None,
                                error="Cancelled due to fail_fast mode",
                                duration_s=0.0,
                                model=self.settings.model,
                                tokens_used=None,
                            )
                            results.append(cancelled_result)
                        break

        return results

    def ask_many_with_retry(
        self,
        prompts: Sequence[str],
        *,
        return_format: Literal["text", "json"] = "text",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> list[AskResult]:
        """Ask multiple questions with retry logic.

        Args:
            prompts: List of prompts to process
            return_format: Format for responses ("text" or "json")
            max_retries: Maximum number of retries per prompt
            retry_delay: Delay between retries in seconds
            **kwargs: Additional parameters

        Returns:
            List of AskResult objects
        """
        import time

        from .models import AskResult

        results = []

        for prompt in prompts:
            start_time = time.time()
            # Initialize error tracking (currently not used but kept for
            # potential debugging)
            _ = None  # Placeholder for last_error

            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    response = self.provider.ask(
                        prompt, return_format=return_format, **kwargs
                    )
                    duration = time.time() - start_time

                    result = AskResult(
                        prompt=prompt,
                        response=response,
                        error=None,
                        duration_s=duration,
                        model=self.settings.model,
                        tokens_used=None,
                    )
                    break

                except Exception as e:
                    # Store last error for potential debugging
                    # (though not currently used)
                    _ = e  # Mark as intentionally unused
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                    else:
                        duration = time.time() - start_time
                        result = AskResult(
                            prompt=prompt,
                            response=None,
                            error=str(e),
                            duration_s=duration,
                            model=self.settings.model,
                            tokens_used=None,
                        )

            results.append(result)

        return results

    def ask_json(
        self, prompt: str, *, max_repairs: int = 1, **kwargs
    ) -> Union[dict, list]:
        """
        Ask a question and return JSON format response with robust parsing.

        This method requests text responses and parses JSON from them, with
        automatic repair attempts if parsing fails. It handles common issues
        like code fences, extra prose, and minor syntax errors.

        Args:
            prompt: Prompt to process. Should ask for structured/JSON data.
            max_repairs: Maximum number of repair attempts if JSON parsing fails
                         (default: 1)
            **kwargs: Additional parameters to override settings:
                     - model: Override the default model
                     - temperature: Override response temperature
                     - max_tokens: Override maximum response tokens

        Returns:
            Union[dict, list]: Parsed JSON response. For simple JSON objects
                              returns dict, for arrays returns list.

        Raises:
            JsonParseError: If valid JSON cannot be parsed after all repair attempts.

        Example:
            client = AiClient()

            # Get structured data
            colors = client.ask_json(
                "List 5 primary colors as JSON array"
            )
            # Returns: ["red", "blue", "green", "yellow", "orange"]

            # Get structured object
            info = client.ask_json(
                "Information about Python as JSON with keys: name, creator, year"
            )
            # Returns: {"name": "Python", "creator": "Guido van Rossum",
            # "year": 1991}

            # With custom parameters
            data = client.ask_json(
                "API endpoints as JSON", temperature=0.1, max_repairs=2
            )
        """
        # Get request params (excluding internal fields)
        request_params = self.settings.model_dump(
            exclude_none=True,
            exclude={
                "api_key",
                "provider",
                "base_url",
                "timeout",
                "request_timeout_s",
                "extra_headers",
                "usage_scope",
                "usage_client_id",
                "update_check_days",
                "cache_enabled",  # Caching configuration field
                "cache_backend",  # Caching configuration field
                "cache_ttl_s",  # Caching configuration field
                "cache_max_temperature",  # Caching configuration field
                "cache_sqlite_path",  # Cache settings, not provider params
                "cache_sqlite_table",  # Cache settings, not provider params
                "cache_sqlite_wal",  # Cache settings, not provider params
                "cache_sqlite_busy_timeout_ms",  # Cache settings, not provider params
                "cache_sqlite_max_entries",  # Cache settings, not provider params
                "cache_sqlite_prune_batch",  # Cache settings, not provider params
                "cache_namespace",  # Cache settings, not provider params
            },
        )
        request_params.update(kwargs)

        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)

        with progress:
            # Build cache key if caching is enabled
            cache_key = None
            if self._should_use_cache(request_params):
                cache_key = self._build_cache_key(
                    "ask_json",
                    prompt=prompt,
                    request_params=request_params,
                    return_format="json",
                    extra={"max_repairs": max_repairs},
                )
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    # Track usage for cached responses too
                    if self.usage_tracker:
                        estimated_tokens = len(str(cached_result)) // 4
                        self.usage_tracker.record_usage(estimated_tokens)
                    return cached_result

            try:
                response_text = self.provider.ask_text(prompt, **request_params)
                parsed_result = parse_json_from_text(response_text)

                # Cache successful parsed result
                if cache_key is not None:
                    self.cache.set(
                        cache_key, parsed_result, ttl_s=self.settings.cache_ttl_s
                    )

                return parsed_result
            except JsonParseError as e:
                if max_repairs <= 0:
                    raise e

                last_response = response_text
                last_error = str(e)

                for _attempt in range(max_repairs):
                    try:
                        repair_prompt = create_repair_prompt(
                            prompt, last_response, last_error
                        )
                        response_text = self.provider.ask_text(
                            repair_prompt, **request_params
                        )
                        parsed_result = parse_json_from_text(response_text)

                        # Cache successful parsed result after repairs
                        if cache_key is not None:
                            self.cache.set(
                                cache_key,
                                parsed_result,
                                ttl_s=self.settings.cache_ttl_s,
                            )

                        return parsed_result
                    except JsonParseError as repair_error:
                        last_response = response_text
                        last_error = str(repair_error)
                        continue

                raise JsonParseError(
                    "Failed to parse JSON after "
                    f"{max_repairs + 1} attempts. Last error: {last_error}",
                    last_response,
                    original_error=e.original_error,
                ) from e

    def ask_typed(
        self, prompt: str, response_model: type[T], *, max_repairs: int = 1, **kwargs
    ) -> T:
        """
        Ask a question and return a typed Pydantic model instance.

        This method combines JSON parsing with Pydantic validation to return
        strongly-typed responses. It handles JSON parsing errors and schema
        validation errors appropriately.

        Args:
            prompt: Prompt to process. Should ask for data matching the
                   response_model schema.
            response_model: Pydantic model class to validate and parse the
                           response into.
            max_repairs: Maximum number of repair attempts if JSON parsing fails
                         (default: 1)
            **kwargs: Additional parameters to override settings:
                     - model: Override the default model
                     - temperature: Override response temperature
                     - max_tokens: Override maximum response tokens

        Returns:
            T: Instance of the response_model with validated data.

        Raises:
            JsonParseError: If valid JSON cannot be parsed after all repair attempts.
            ValidationError: If JSON parses successfully but doesn't match the
                           response_model schema.

        Example:
            from pydantic import BaseModel

            class Person(BaseModel):
                name: str
                age: int
                email: Optional[str] = None

            client = AiClient()
            person = client.ask_typed(
                "Create a person named Alice, age 30",
                response_model=Person
            )
            # Returns: Person(name="Alice", age=30, email=None)

            # With custom parameters
            person = client.ask_typed(
                "Create a person named Bob",
                response_model=Person,
                max_repairs=2,
                temperature=0.1
            )
        """
        # Get JSON data using ask_json
        json_data = self.ask_json(prompt, max_repairs=max_repairs, **kwargs)

        # Validate with Pydantic model
        try:
            return response_model.model_validate(json_data)
        except ValidationError as e:
            # Re-raise ValidationError without swallowing it
            raise e

    def get_embeddings(
        self,
        texts: list[str],
        *,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        **kwargs,
    ) -> list[list[float]]:
        """
        Get embeddings for a list of texts.

        Args:
            texts: List of text strings to get embeddings for
            model: Optional embedding model override (defaults to
                  text-embedding-3-small)
            dimensions: Optional embedding dimensions (for models that support it)
            **kwargs: Additional parameters to override settings

        Returns:
            list[list[float]]: List of embedding vectors, one per input text

        Example:
            client = AiClient()
            embeddings = client.get_embeddings(["Hello", "World"])
            print(
                f"Got {len(embeddings)} embeddings of {len(embeddings[0])} "
                "dimensions each"
            )
        """
        # Get request params (excluding internal fields)
        request_params = self.settings.model_dump(
            exclude_none=True,
            exclude={
                "api_key",
                "provider",
                "base_url",
                "timeout",
                "request_timeout_s",
                "extra_headers",
                "usage_scope",
                "usage_client_id",
                "update_check_days",
                "cache_enabled",  # Caching configuration field
                "cache_backend",  # Caching configuration field
                "cache_ttl_s",  # Caching configuration field
                "cache_max_temperature",  # Caching configuration field
                "cache_sqlite_path",  # Cache settings, not provider params
                "cache_sqlite_table",  # Cache settings, not provider params
                "cache_sqlite_wal",  # Cache settings, not provider params
                "cache_sqlite_busy_timeout_ms",  # Cache settings, not provider params
                "cache_sqlite_max_entries",  # Cache settings, not provider params
                "cache_sqlite_prune_batch",  # Cache settings, not provider params
                "cache_namespace",  # Cache settings, not provider params
            },
        )
        request_params.update(kwargs)

        # Use specified model or default embedding model
        embedding_model = model or "text-embedding-3-small"

        # Check cache
        cache_key = None
        if self._should_use_cache(request_params):
            cache_key = self._build_cache_key(
                "embeddings",
                prompt="",  # Empty prompt for embeddings
                request_params={**request_params, "model": embedding_model},
                return_format="embeddings",
                extra={
                    "texts": texts,  # Include all texts for cache key
                    "dimensions": dimensions,
                },
            )
            cached_embeddings = self.cache.get(cache_key)
            if cached_embeddings is not None:
                # Track usage for cached responses too
                if self.usage_tracker:
                    estimated_tokens = sum(
                        len(text) for text in texts
                    )  # Rough estimate
                    self.usage_tracker.record_usage(estimated_tokens)
                return cached_embeddings

        # Show progress indicator if enabled
        progress = ProgressIndicator(show=self.show_progress)

        # Validate API key before creating OpenAI client
        if not self.settings.api_key:
            raise ValueError("API key is required for embeddings")

        with progress:
            # OpenAI is already imported at module level
            openai_client = OpenAI(
                api_key=self.settings.api_key,
                base_url=self.settings.base_url,
                timeout=self.settings.timeout,
            )

            # Make embeddings request
            openai_kwargs: dict[str, Any] = {"model": embedding_model, "input": texts}
            if dimensions is not None:
                openai_kwargs["dimensions"] = dimensions
            response = openai_client.embeddings.create(**openai_kwargs)

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]

            # Cache successful response
            if cache_key is not None:
                self.cache.set(cache_key, embeddings, ttl_s=self.settings.cache_ttl_s)

        # Track usage if enabled
        if self.usage_tracker:
            estimated_tokens = sum(len(text) for text in texts)  # Rough estimate
            self.usage_tracker.record_usage(estimated_tokens)

        return embeddings

    def upload_file(
        self,
        path: Path,
        *,
        purpose: str = "assistants",
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> UploadedFile:
        """Upload a file to the AI provider.

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
            >>> file = client.upload_file("document.pdf", purpose="assistants")
            >>> print(f"Uploaded: {file.file_id}")
        """
        # Validate input
        if not isinstance(path, Path):
            path = Path(path)

        if not path.exists():
            raise ValueError(f"File does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Delegate to provider
        try:
            return self.provider.upload_file(
                path, purpose=purpose, filename=filename, mime_type=mime_type
            )
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError(
                "upload", self.provider.__class__.__name__, e
            ) from e

    def download_file(
        self, file_id: str, *, to_path: Optional[Path] = None
    ) -> Union[bytes, Path]:
        """Download file content from the AI provider.

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
            >>> content = client.download_file("file-123")
            >>>
            >>> # Download to file
            >>> path = client.download_file("file-123", to_path="downloaded.pdf")
        """
        if not file_id:
            raise ValueError("file_id cannot be empty")

        # Delegate to provider
        try:
            content = self.provider.download_file(file_id)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError(
                "download", self.provider.__class__.__name__, e
            ) from e

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

    def generate_image(
        self,
        prompt: str,
        *,
        size: Literal[
            "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
        ] = "1024x1024",
        quality: Literal["standard", "hd"] = "standard",
        n: int = 1,
    ) -> list[str]:
        """Generate images using AI.

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
            >>> urls = client.generate_image("A cute dog playing fetch")
            >>>
            >>> # Generate multiple high-quality images
            >>> urls = client.generate_image(
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

        # Delegate to provider
        try:
            return self.provider.generate_image(prompt, size=size, quality=quality, n=n)
        except ProviderCapabilityError:
            # Re-raise with more context
            raise
        except Exception as e:
            if isinstance(e, FileTransferError):
                # Re-raise FileTransferError as-is
                raise
            # Wrap other exceptions
            raise FileTransferError(
                "image generation", self.provider.__class__.__name__, e
            ) from e

    def transcribe_audio(
        self,
        audio_file: Union[str, Path],
        language: Optional[str] = None,
        model: str = "whisper-1",
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "json",
    ) -> dict[str, Any]:
        """
        Transcribe audio file to text using AI models.

        Args:
            audio_file: Path to audio file to transcribe
            language: Optional language code (e.g., 'en', 'es')
            model: Transcription model to use (default: 'whisper-1')
            prompt: Optional prompt to guide transcription
            temperature: Sampling temperature (0.0 to 1.0)
            response_format: Response format ('json', 'text', 'srt',
                           'verbose_json', 'vtt')

        Returns:
            Dictionary containing transcription results

        Raises:
            FileTransferError: If transcription fails

        Example:
            result = client.transcribe_audio("recording.wav")
            print(result["text"])
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor

            # Create audio processor with this client
            processor = AudioProcessor(client=self)

            # Perform transcription
            result = processor.transcribe_audio(
                audio_file=audio_file,
                language=language,
                model=model,
                prompt=prompt,
                temperature=temperature,
                response_format=response_format,
            )

            # Convert to dictionary for API consistency
            return {
                "text": result.text,
                "language": result.language,
                "duration_seconds": result.duration_seconds,
                "model_used": result.model_used,
                "processing_time_seconds": result.processing_time_seconds,
                "word_count": result.word_count,
                "character_count": result.character_count,
                "segments": [
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                        "confidence": seg.confidence,
                    }
                    for seg in (result.segments or [])
                ],
                "metadata": result.metadata,
            }

        except Exception as e:
            raise FileTransferError(
                "audio transcription", self.provider.__class__.__name__, e
            ) from e

    def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes:
        """
        Generate audio from text using text-to-speech.

        Args:
            text: Text to convert to speech
            voice: Voice to use for generation (default: 'alloy')
            model: Text-to-speech model (default: 'tts-1')
            speed: Speech speed factor (0.25 to 4.0)
            response_format: Output audio format ('mp3', 'wav', 'flac', 'ogg', 'webm')

        Returns:
            Generated audio data as bytes

        Raises:
            FileTransferError: If audio generation fails

        Example:
            audio_data = client.generate_audio("Hello, world!", voice="nova")
            # Save to a proper output path (not repository root)
            with open("output.mp3", "wb") as f:
                f.write(audio_data)
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_models import AudioFormat
            from .audio.audio_processor import AudioProcessor

            # Create audio processor with this client
            processor = AudioProcessor(client=self)

            # Convert string format to enum
            format_map = {
                "mp3": AudioFormat.MP3,
                "wav": AudioFormat.WAV,
                "flac": AudioFormat.FLAC,
                "ogg": AudioFormat.OGG,
                "webm": AudioFormat.WEBM,
            }

            if response_format not in format_map:
                raise ValueError(f"Invalid audio format: {response_format}")

            # Perform generation
            result = processor.generate_audio(
                text=text,
                voice=voice,
                model=model,
                speed=speed,
                response_format=format_map[response_format],
            )

            return result.audio_data

        except Exception as e:
            raise FileTransferError(
                "audio generation", self.provider.__class__.__name__, e
            ) from e

    def get_audio_voices(self) -> list[dict[str, str]]:
        """
        Get list of available voices for audio generation.

        Returns:
            List of voice information dictionaries

        Raises:
            FileTransferError: If voice retrieval fails
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor

            processor = AudioProcessor(client=self)
            voices_info = processor.get_supported_voices()

            return voices_info.get("voices", [])

        except Exception as e:
            raise FileTransferError(
                "audio voices", self.provider.__class__.__name__, e
            ) from e

    def validate_audio_file(self, audio_file: Union[str, Path]) -> dict[str, Any]:
        """
        Validate audio file for transcription requirements.

        Args:
            audio_file: Path to audio file to validate

        Returns:
            Dictionary with validation results

        Raises:
            FileTransferError: If validation fails
        """
        try:
            # Import here to avoid circular imports
            from .audio.audio_processor import AudioProcessor

            processor = AudioProcessor(client=self)
            return processor.validate_audio_for_transcription(audio_file)

        except Exception as e:
            raise FileTransferError(
                "audio validation", self.provider.__class__.__name__, e
            ) from e

    def _ensure_knowledge_enabled(self):
        """Ensure knowledge functionality is enabled."""
        if not self.settings.knowledge_enabled:
            from .knowledge.exceptions import KnowledgeDisabledError

            raise KnowledgeDisabledError(
                "Knowledge functionality is disabled. Set "
                "AI_KNOWLEDGE_ENABLED=true to enable."
            )

    def _get_knowledge_config(self):
        """Get knowledge configuration from settings."""
        from pathlib import Path

        from .config_models import KnowledgeConfig

        # Convert string paths to Path objects
        roots = []
        if self.settings.knowledge_roots:
            roots = [
                Path(root.strip())
                for root in self.settings.knowledge_roots.split(",")
                if root.strip()
            ]

        db_path = (
            Path(self.settings.knowledge_db_path)
            if self.settings.knowledge_db_path
            else Path("knowledge.db")
        )

        return KnowledgeConfig(
            knowledge_enabled=self.settings.knowledge_enabled,
            knowledge_db_path=db_path,
            knowledge_roots=roots,
            embedding_model=self.settings.embedding_model,
            chunk_size=self.settings.knowledge_chunk_size or 1000,
            chunk_overlap=self.settings.knowledge_chunk_overlap or 200,
            min_chunk_size=self.settings.knowledge_min_chunk_size or 100,
            max_file_size=self.settings.knowledge_max_file_size or (10 * 1024 * 1024),
            use_sqlite_extension=self.settings.knowledge_use_sqlite_extension,
        )

    def index_knowledge(
        self,
        directory: Optional[Union[str, Path]] = None,
        force_reindex: bool = False,
        recursive: bool = True,
    ) -> dict[str, Any]:
        """
        Index knowledge from files into the vector database.

        Args:
            directory: Directory to index (uses knowledge_roots from settings if None)
            force_reindex: Whether to force reindexing all files
            recursive: Whether to search subdirectories

        Returns:
            Dictionary with indexing statistics

        Raises:
            KnowledgeDisabledError: If knowledge functionality is disabled
            KnowledgeIndexError: If indexing fails
        """
        self._ensure_knowledge_enabled()

        try:
            # Get knowledge configuration
            knowledge_config = self._get_knowledge_config()

            # Import knowledge components
            from .knowledge.backend import SqliteVectorBackend
            from .knowledge.chunking import TextChunker
            from .knowledge.indexer import KnowledgeIndexer
            from .knowledge.sources import FileSourceLoader

            # Initialize components
            backend = SqliteVectorBackend(
                db_path=knowledge_config.knowledge_db_path,
                embedding_dimension=1536,  # OpenAI embedding dimension
                vector_extension=knowledge_config.vector_extension,
            )

            file_loader = FileSourceLoader(max_file_size=knowledge_config.max_file_size)

            chunker = TextChunker(
                chunk_size=knowledge_config.chunk_size,
                chunk_overlap=knowledge_config.chunk_overlap,
                min_chunk_size=knowledge_config.min_chunk_size,
            )

            indexer = KnowledgeIndexer(
                backend=backend,
                file_loader=file_loader,
                chunker=chunker,
                embedding_client=self,
                embedding_model=knowledge_config.embedding_model,
            )

            # Determine what to index
            if directory:
                directory = Path(directory)
                stats = indexer.index_directory(
                    directory, recursive=recursive, force_reindex=force_reindex
                )
            else:
                # Index all configured roots
                all_stats = {
                    "total_files": 0,
                    "processed_files": 0,
                    "skipped_files": 0,
                    "error_files": 0,
                    "total_chunks": 0,
                    "total_embeddings": 0,
                    "processing_time": 0.0,
                    "errors": [],
                }

                for root_dir in knowledge_config.knowledge_roots:
                    root_path = Path(root_dir)
                    if root_path.exists():
                        stats = indexer.index_directory(
                            root_path, recursive=recursive, force_reindex=force_reindex
                        )

                        # Aggregate statistics
                        for key in all_stats:
                            if key == "errors":
                                all_stats[key].extend(stats.get(key, []))
                            elif isinstance(all_stats[key], (int, float)):
                                all_stats[key] += stats.get(key, 0)

                stats = all_stats

            return stats

        except Exception as e:
            from .knowledge.exceptions import KnowledgeIndexError

            raise KnowledgeIndexError(f"Knowledge indexing failed: {e}", cause=e) from e

    def search_knowledge(
        self, query: str, top_k: int = 5, similarity_threshold: float = 0.0
    ) -> list[dict[str, Any]]:
        """
        Search the knowledge base for relevant information.

        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of search results with chunk content and metadata

        Raises:
            KnowledgeDisabledError: If knowledge functionality is disabled
            KnowledgeSearchError: If search fails
        """
        self._ensure_knowledge_enabled()

        try:
            # Get knowledge configuration
            knowledge_config = self._get_knowledge_config()

            # Import knowledge components
            from .knowledge.backend import SqliteVectorBackend
            from .knowledge.search import KnowledgeSearch

            # Initialize components
            backend = SqliteVectorBackend(
                db_path=knowledge_config.knowledge_db_path,
                embedding_dimension=1536,
                vector_extension=knowledge_config.vector_extension,
            )

            search = KnowledgeSearch(
                backend=backend,
                embedding_client=self,
                embedding_model=knowledge_config.embedding_model,
            )

            # Perform search
            hits = search.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            # Convert to dictionaries
            results = []
            for hit in hits:
                results.append(
                    {
                        "text": hit.text,
                        "similarity_score": hit.similarity_score,
                        "rank": hit.rank,
                        "source_path": str(hit.source_path),
                        "source_type": hit.source_type,
                        "chunk_id": hit.chunk.chunk_id,
                        "chunk_index": hit.chunk.chunk_index,
                        "metadata": hit.chunk.metadata,
                    }
                )

            return results

        except Exception as e:
            from .knowledge.exceptions import KnowledgeSearchError

            raise KnowledgeSearchError(f"Knowledge search failed: {e}", cause=e) from e

    def ask_with_knowledge(
        self,
        prompt: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        max_context_chars: int = 4000,
        **kwargs,
    ) -> "AskResult":
        """
        Ask a question with knowledge context retrieved from the indexed documents.

        Args:
            prompt: The question or prompt
            top_k: Number of knowledge chunks to retrieve
            similarity_threshold: Minimum similarity threshold for knowledge retrieval
            max_context_chars: Maximum total characters for knowledge context
                              (default: 4000)
            **kwargs: Additional arguments passed to ask()

        Returns:
            AskResult with AI response that includes knowledge context

        Raises:
            KnowledgeDisabledError: If knowledge functionality is disabled
            KnowledgeSearchError: If knowledge retrieval fails
        """
        self._ensure_knowledge_enabled()

        # Retrieve relevant knowledge
        knowledge_results = self.search_knowledge(
            query=prompt,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        # Apply guardrails to knowledge results
        processed_results = self._process_knowledge_results(
            knowledge_results, max_context_chars=max_context_chars
        )

        # Format knowledge context with compact metadata
        if processed_results:
            context_parts = []
            for i, result in enumerate(processed_results, 1):
                # Extract file name and heading from metadata if available
                file_name = Path(result["source_path"]).name
                heading = ""
                if result.get("metadata") and "heading" in result["metadata"]:
                    heading = f" - {result['metadata']['heading']}"

                # Compact format with file, heading, and chunk ID
                context_parts.append(
                    f"[{i}] {file_name}{heading} (chunk "
                    f"{result.get('chunk_id', 'unknown').split(':')[-1]})\n"
                    f"{result['text']}"
                )

            knowledge_context = "\n\n".join(context_parts)

            # Create enhanced prompt with knowledge context
            enhanced_prompt = (
                f"Context from relevant documents:\n\n"
                f"{knowledge_context}\n\n"
                f"Based on the above context, please answer: {prompt}\n\n"
                f"If the context doesn't contain relevant information, "
                f"please say so and provide the best answer you can."
            )
        else:
            # No relevant knowledge found
            enhanced_prompt = (
                f"No relevant information found in the knowledge base. "
                f"Please answer: {prompt}"
            )

        # Get AI response with enhanced prompt
        response_text = self.ask(enhanced_prompt, **kwargs)

        # Create AskResult with knowledge metadata
        from .models import AskResult

        result = AskResult(
            prompt=enhanced_prompt,
            response=response_text,
            error=None,
            duration_s=0.0,  # Could track timing if needed
            knowledge_used=len(processed_results) > 0,
            knowledge_sources=[r["source_path"] for r in processed_results],
            knowledge_count=len(processed_results),
        )

        return result

    def _process_knowledge_results(
        self, results: list[dict], max_context_chars: int
    ) -> list[dict]:
        """
        Apply guardrails to knowledge results:
        - Deduplicate near-identical chunks
        - Limit total character count
        - Prioritize by similarity score
        """
        if not results:
            return []

        # 1. Deduplicate near-identical chunks
        deduped_results = self._deduplicate_chunks(results)

        # 2. Sort by similarity score (highest first)
        deduped_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        # 3. Apply character limit
        limited_results = []
        total_chars = 0

        for result in deduped_results:
            # Estimate characters needed for this result (including metadata)
            text_chars = len(result["text"])
            metadata_chars = 100  # Rough estimate for metadata formatting
            estimated_chars = text_chars + metadata_chars

            if total_chars + estimated_chars <= max_context_chars:
                limited_results.append(result)
                total_chars += estimated_chars
            else:
                # Try to fit a truncated version if it's the first result
                if (
                    not limited_results
                    and text_chars > max_context_chars - metadata_chars
                ):
                    # Truncate the text to fit
                    max_text = (
                        max_context_chars - metadata_chars - 20
                    )  # Leave room for "..."
                    truncated = result["text"][:max_text] + "..."
                    result_copy = result.copy()
                    result_copy["text"] = truncated
                    limited_results.append(result_copy)
                    total_chars = max_context_chars
                break

        # 4. Sort back by original ranking (similarity)
        limited_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return limited_results

    def _deduplicate_chunks(self, results: list[dict]) -> list[dict]:
        """
        Remove near-identical chunks based on text similarity.
        Uses simple heuristics to avoid duplicate content.
        """
        if not results:
            return []

        deduped = []
        seen_texts = set()

        for result in results:
            text = (result["text"] or "").strip()

            # Simple deduplication checks
            is_duplicate = False

            # Check exact matches
            if text in seen_texts:
                is_duplicate = True
            else:
                # Check for near-duplicates using multiple strategies
                for seen_text in seen_texts:
                    # Strategy 1: Check if large portion of text is identical
                    # Find longest common substring
                    common = self._longest_common_substring(text, seen_text)
                    if common and len(common) > 80:  # Substantial common content
                        # Check if common content is a significant portion of both texts
                        ratio1 = len(common) / len(text)
                        ratio2 = len(common) / len(seen_text)
                        if ratio1 > 0.35 and ratio2 > 0.35:  # Lowered from 0.5
                            is_duplicate = True
                            break

                    # Strategy 2: Check word-level similarity for shorter chunks
                    if len(text) < 500 and len(seen_text) < 500:
                        words1 = set(text.lower().split())
                        words2 = set(seen_text.lower().split())
                        if words1 and words2:
                            intersection = words1.intersection(words2)
                            union = words1.union(words2)
                            similarity = len(intersection) / len(union)
                            if similarity > 0.65:  # Lowered from 0.7
                                is_duplicate = True
                                break

            if not is_duplicate:
                deduped.append(result)
                seen_texts.add(text)

        return deduped

    def _longest_common_substring(self, s1: str, s2: str) -> str:
        """Find the longest common substring between two strings."""
        # Simple implementation - good enough for deduplication
        m = len(s1)
        n = len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        max_length = 0
        end_pos = 0

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    if dp[i][j] > max_length:
                        max_length = dp[i][j]
                        end_pos = i
                else:
                    dp[i][j] = 0

        return s1[end_pos - max_length : end_pos] if max_length > 0 else ""


# Convenience function for backward compatibility
def create_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    show_progress: bool = True,
    **kwargs,
) -> AiClient:
    """Create an AiClient with explicit parameters.

    Args:
        api_key: API key to use (required for most providers)
        model: Model name to use (required)
        show_progress: Whether to show progress indicators
        **kwargs: Additional settings parameters

                 - base_url: Custom API base URL

    Returns:
        AiClient: Configured AI client ready for use

    Raises:
        ProviderConfigurationError: If required configuration is missing

    Note:
        For interactive setup, run 'ai-utilities setup' command instead.
    """
    # Create settings first
    settings = AiSettings(model=model, **kwargs)

    # If explicit API key is provided, use it
    if api_key is not None:
        settings.api_key = api_key

    # Create client - the provider factory will handle API key resolution if needed
    return AiClient(settings, show_progress=show_progress)
