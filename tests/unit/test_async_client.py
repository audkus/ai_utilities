"""Comprehensive tests for async_client.py module - Phase 7B.

This module provides thorough testing for the AsyncAiClient and AsyncOpenAIProvider,
covering all async operations, concurrency control, retry logic, and error handling.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_utilities.async_client import AsyncAiClient, AsyncOpenAIProvider
from ai_utilities.client import AiSettings
from ai_utilities.file_models import UploadedFile
from ai_utilities.providers.provider_exceptions import (
    FileTransferError,
    ProviderCapabilityError,
)


class TestAsyncOpenAIProvider:
    """Test the AsyncOpenAIProvider class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock AI settings."""
        return AiSettings(api_key="test_key", model="gpt-3.5-turbo")

    @pytest.fixture
    def async_provider(self, mock_settings):
        """Create AsyncOpenAIProvider instance."""
        # Mock OpenAIProvider class to avoid import dependency
        mock_sync_instance = MagicMock()
        mock_sync_instance.ask.return_value = "Test response"
        mock_sync_instance.ask_many.return_value = ["Response 1", "Response 2"]
        
        # Patch the _get_openai function to prevent the import error
        with patch('ai_utilities.providers.openai_provider._get_openai'):
            provider = AsyncOpenAIProvider(mock_settings)
            # Replace the internal sync provider with our mock
            provider._sync_provider = mock_sync_instance
            return provider, mock_sync_instance

    @pytest.mark.asyncio
    async def test_async_provider_ask(self, async_provider):
        """Test async ask method."""
        provider, mock_sync = async_provider

        # Mock sync provider response
        mock_sync.ask.return_value = "Test response"

        # Test async ask
        result = await provider.ask("Test prompt")

        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty response
        mock_sync.ask.assert_called_once_with("Test prompt", return_format="text")

    @pytest.mark.asyncio
    async def test_async_provider_ask_json(self, async_provider):
        """Test async ask method with JSON format."""
        provider, mock_sync = async_provider

        # Mock sync provider response
        mock_sync.ask.return_value = {"key": "value"}

        # Test async ask with JSON
        result = await provider.ask("Test prompt", return_format="json")

        assert result == {"key": "value"}
        mock_sync.ask.assert_called_once_with("Test prompt", return_format="json")

    @pytest.mark.asyncio
    async def test_async_provider_ask_many(self, async_provider):
        """Test async ask_many method."""
        provider, mock_sync = async_provider

        # Mock sync provider response
        mock_sync.ask_many.return_value = ["Response 1", "Response 2"]

        # Test async ask_many
        prompts = ["Prompt 1", "Prompt 2"]
        result = await provider.ask_many(prompts)

        assert result == ["Response 1", "Response 2"]
        mock_sync.ask_many.assert_called_once_with(prompts, return_format="text")

    @pytest.mark.asyncio
    async def test_async_provider_upload_file(self, async_provider):
        """Test async upload_file method."""
        provider, mock_sync = async_provider

        # Mock sync provider response
        mock_file = UploadedFile(file_id="file_123", filename="test.txt", bytes=100, provider="test_provider")
        mock_sync.upload_file.return_value = mock_file

        # Test async upload
        test_path = Path("test.txt")
        result = await provider.upload_file(test_path)

        assert result == mock_file
        mock_sync.upload_file.assert_called_once_with(
            test_path, purpose="assistants", filename=None, mime_type=None
        )

    @pytest.mark.asyncio
    async def test_async_provider_download_file(self, async_provider):
        """Test async download_file method."""
        provider, mock_sync = async_provider

        # Mock sync provider response
        mock_sync.download_file.return_value = b"file content"

        # Test async download
        result = await provider.download_file("file_123")

        assert result == b"file content"
        mock_sync.download_file.assert_called_once_with("file_123")

    @pytest.mark.asyncio
    async def test_async_provider_generate_image(self, async_provider):
        """Test async generate_image method."""
        provider, mock_sync = async_provider

        # Mock sync provider response
        mock_sync.generate_image.return_value = ["url1", "url2"]

        # Test async image generation
        result = await provider.generate_image("Test prompt", n=2)

        assert result == ["url1", "url2"]
        mock_sync.generate_image.assert_called_once_with(
            "Test prompt", size="1024x1024", quality="standard", n=2
        )


class TestAsyncAiClient:
    """Test the AsyncAiClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock AI settings."""
        return AiSettings(api_key="test_key", model="gpt-3.5-turbo")

    @pytest.fixture
    def mock_provider(self):
        """Create mock async provider."""
        provider = AsyncMock()
        provider.ask.return_value = "Test response"
        provider.upload_file.return_value = UploadedFile(file_id="file_123", filename="test.txt", bytes=100, provider="test_provider")
        provider.download_file.return_value = b"file content"
        provider.generate_image.return_value = ["url1"]
        return provider

    @pytest.fixture
    def async_client(self, mock_settings, mock_provider):
        """Create AsyncAiClient instance with mock provider."""
        return AsyncAiClient(settings=mock_settings, provider=mock_provider)

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_settings, mock_provider):
        """Test AsyncAiClient initialization."""
        client = AsyncAiClient(settings=mock_settings, provider=mock_provider)

        assert client.settings == mock_settings
        assert client.provider == mock_provider
        assert client.show_progress is True

    @pytest.mark.asyncio
    async def test_client_initialization_defaults(self, openai_mocks):
        """Test AsyncAiClient initialization with defaults."""
        from tests.fake_provider import FakeAsyncProvider
        
        fake_async_provider = FakeAsyncProvider()
        client = AsyncAiClient(provider=fake_async_provider)

        assert client.settings is not None
        assert client.provider is fake_async_provider
        assert client.show_progress is True

    @pytest.mark.asyncio
    async def test_ask_success(self, async_client, mock_provider):
        """Test successful ask operation."""
        result = await async_client.ask("Test prompt")

        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty response
        mock_provider.ask.assert_called_once_with("Test prompt", return_format="text")

    @pytest.mark.asyncio
    async def test_ask_json_format(self, async_client, mock_provider):
        """Test ask operation with JSON format."""
        mock_provider.ask.return_value = {"key": "value"}

        result = await async_client.ask("Test prompt", return_format="json")

        assert result == {"key": "value"}
        mock_provider.ask.assert_called_once_with("Test prompt", return_format="json")

    @pytest.mark.asyncio
    async def test_ask_with_exception(self, async_client, mock_provider):
        """Test ask operation with provider exception."""
        mock_provider.ask.side_effect = Exception("Provider error")

        with pytest.raises(Exception, match="Provider error"):
            await async_client.ask("Test prompt")

    @pytest.mark.asyncio
    async def test_ask_many_empty_list(self, async_client):
        """Test ask_many with empty prompt list."""
        result = await async_client.ask_many([])

        assert result == []

    @pytest.mark.asyncio
    async def test_ask_many_success(self, async_client, mock_provider):
        """Test successful ask_many operation."""
        prompts = ["Prompt 1", "Prompt 2"]
        mock_provider.ask.return_value = "Response for {prompt}"

        # Mock the provider to return different responses
        async def mock_ask(prompt, **kwargs):
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        results = await async_client.ask_many(prompts, concurrency=2)

        assert len(results) == 2
        assert results[0].prompt == "Prompt 1"
        assert results[0].response == "Response for Prompt 1"
        assert results[0].error is None
        assert results[0].model == "gpt-3.5-turbo"
        assert results[1].prompt == "Prompt 2"
        assert results[1].response == "Response for Prompt 2"
        assert results[1].error is None

    @pytest.mark.asyncio
    async def test_ask_many_with_errors(self, async_client, mock_provider):
        """Test ask_many with some provider errors."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        async def mock_ask(prompt, **kwargs):
            if prompt == "Prompt 2":
                raise Exception("Provider error")
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        results = await async_client.ask_many(prompts, concurrency=2)

        assert len(results) == 3
        assert results[0].error is None
        assert results[1].error == "Provider error"
        assert results[2].error is None

    @pytest.mark.asyncio
    async def test_ask_many_fail_fast(self, async_client, mock_provider):
        """Test ask_many with fail_fast enabled."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        async def mock_ask(prompt, **kwargs):
            if prompt == "Prompt 2":
                raise Exception("Provider error")
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        results = await async_client.ask_many(prompts, fail_fast=True)

        # Should stop after first error
        assert len(results) == 3
        assert results[0].error is None
        assert results[1].error == "Provider error"
        # Results after error should be canceled or have errors
        assert results[2].error is not None

    @pytest.mark.asyncio
    async def test_ask_many_with_progress_callback(self, async_client, mock_provider):
        """Test ask_many with progress callback."""
        prompts = ["Prompt 1", "Prompt 2"]
        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        mock_provider.ask.return_value = "Response"

        await async_client.ask_many(prompts, on_progress=progress_callback)

        # Should have called progress callback
        assert len(progress_calls) > 0
        assert all(completed <= total for completed, total in progress_calls)

    @pytest.mark.asyncio
    async def test_ask_many_progress_callback_error(self, async_client, mock_provider):
        """Test ask_many handles progress callback errors gracefully."""
        prompts = ["Prompt 1", "Prompt 2"]

        def failing_progress_callback(completed, total):
            raise ValueError("Callback error")

        mock_provider.ask.return_value = "Response"

        # Should not raise exception due to progress callback error
        results = await async_client.ask_many(prompts, on_progress=failing_progress_callback)

        assert len(results) == 2
        assert all(r.error is None for r in results)

    @pytest.mark.asyncio
    async def test_ask_many_concurrency_control(self, async_client, mock_provider):
        """Test ask_many respects concurrency limits."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3", "Prompt 4", "Prompt 5"]

        # Track concurrent calls
        concurrent_count = 0
        max_concurrent = 0

        async def mock_ask(prompt, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Simulate work
            concurrent_count -= 1
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        results = await async_client.ask_many(prompts, concurrency=2)

        assert len(results) == 5
        assert max_concurrent <= 2  # Should not exceed concurrency limit

    @pytest.mark.asyncio
    async def test_ask_many_with_retry_empty(self, async_client):
        """Test ask_many_with_retry with empty list."""
        result = await async_client.ask_many_with_retry([])

        assert result == []

    @pytest.mark.asyncio
    async def test_ask_many_with_retry_success(self, async_client, mock_provider):
        """Test ask_many_with_retry with successful requests."""
        prompts = ["Prompt 1", "Prompt 2"]
        mock_provider.ask.return_value = "Response"

        results = await async_client.ask_many_with_retry(prompts, max_retries=2)

        assert len(results) == 2
        assert all(r.error is None for r in results)

    @pytest.mark.asyncio
    async def test_ask_many_with_retry_retryable_errors(self, async_client, mock_provider):
        """Test ask_many_with_retry with retryable errors."""
        prompts = ["Prompt 1", "Prompt 2"]

        # Track call counts
        call_counts = {"Prompt 1": 0, "Prompt 2": 0}

        async def mock_ask(prompt, **kwargs):
            call_counts[prompt] += 1
            if prompt == "Prompt 1" and call_counts[prompt] == 1:
                raise Exception("Rate limit exceeded")
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        with patch('asyncio.sleep'):  # Speed up test by skipping sleep
            results = await async_client.ask_many_with_retry(prompts, max_retries=2)

        assert len(results) == 2
        assert results[0].error is None  # Should succeed after retry
        assert results[1].error is None
        assert call_counts["Prompt 1"] == 2  # Should have retried

    @pytest.mark.asyncio
    async def test_ask_many_with_retry_non_retryable_errors(self, async_client, mock_provider):
        """Test ask_many_with_retry with non-retryable errors."""
        prompts = ["Prompt 1", "Prompt 2"]

        async def mock_ask(prompt, **kwargs):
            if prompt == "Prompt 1":
                raise Exception("Invalid prompt format")
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        results = await async_client.ask_many_with_retry(prompts, max_retries=2)

        assert len(results) == 2
        assert results[0].error is not None  # Should not retry
        assert results[1].error is None

    @pytest.mark.asyncio
    async def test_ask_many_with_retry_max_retries_exceeded(self, async_client, mock_provider):
        """Test ask_many_with_retry when max retries exceeded."""
        prompts = ["Prompt 1"]

        mock_provider.ask.side_effect = Exception("Rate limit exceeded")

        with patch('asyncio.sleep'):  # Speed up test
            results = await async_client.ask_many_with_retry(prompts, max_retries=2)

        assert len(results) == 1
        assert results[0].error == "Rate limit exceeded"

    @pytest.mark.asyncio
    async def test_upload_file_success(self, async_client, mock_provider):
        """Test successful file upload."""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = Path(temp_file.name)

            result = await async_client.upload_file(temp_path)

            assert result.file_id == "file_123"
            mock_provider.upload_file.assert_called_once_with(
                temp_path, purpose="assistants", filename=None, mime_type=None
            )

    @pytest.mark.asyncio
    async def test_upload_file_nonexistent_path(self, async_client):
        """Test upload_file with nonexistent path."""
        nonexistent_path = Path("/nonexistent/file.txt")

        with pytest.raises(ValueError, match="File does not exist"):
            await async_client.upload_file(nonexistent_path)

    @pytest.mark.asyncio
    async def test_upload_file_directory_path(self, async_client):
        """Test upload_file with directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)

            with pytest.raises(ValueError, match="Path is not a file"):
                await async_client.upload_file(dir_path)

    @pytest.mark.asyncio
    async def test_upload_file_provider_capability_error(self, async_client, mock_provider):
        """Test upload_file with provider capability error."""
        mock_provider.upload_file.side_effect = ProviderCapabilityError("upload", "TestProvider")

        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(ProviderCapabilityError):
                await async_client.upload_file(Path(temp_file.name))

    @pytest.mark.asyncio
    async def test_upload_file_file_transfer_error(self, async_client, mock_provider):
        """Test upload_file with file transfer error."""
        mock_provider.upload_file.side_effect = FileTransferError("upload", "provider", Exception("Upload failed"))

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = Path(temp_file.name)

            with pytest.raises(FileTransferError):
                await async_client.upload_file(temp_path)

    @pytest.mark.asyncio
    async def test_upload_file_wrapped_exception(self, async_client, mock_provider):
        """Test upload_file wraps other exceptions."""
        mock_provider.upload_file.side_effect = Exception("Generic error")

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = Path(temp_file.name)

            with pytest.raises(FileTransferError) as exc_info:
                await async_client.upload_file(temp_path)

            assert "upload" in str(exc_info.value)
            assert "Generic error" in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_download_file_success_bytes(self, async_client, mock_provider):
        """Test successful file download as bytes."""
        result = await async_client.download_file("file_123")

        assert result == b"file content"
        mock_provider.download_file.assert_called_once_with("file_123")

    @pytest.mark.asyncio
    async def test_download_file_success_to_path(self, async_client, mock_provider):
        """Test successful file download to path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / "downloaded.txt"

            result = await async_client.download_file("file_123", to_path=target_path)

            assert result == target_path
            assert target_path.exists()
            assert target_path.read_bytes() == b"file content"

    @pytest.mark.asyncio
    async def test_download_file_empty_id(self, async_client):
        """Test download_file with empty file_id."""
        with pytest.raises(ValueError, match="file_id cannot be empty"):
            await async_client.download_file("")

    @pytest.mark.asyncio
    async def test_download_file_provider_capability_error(self, async_client, mock_provider):
        """Test download_file with provider capability error."""
        mock_provider.download_file.side_effect = ProviderCapabilityError("download", "TestProvider")

        with pytest.raises(ProviderCapabilityError):
            await async_client.download_file("file_123")

    @pytest.mark.asyncio
    async def test_download_file_wrapped_exception(self, async_client, mock_provider):
        """Test download_file wraps other exceptions."""
        mock_provider.download_file.side_effect = Exception("Generic error")

        with pytest.raises(FileTransferError) as exc_info:
            await async_client.download_file("file_123")

        assert "download" in str(exc_info.value)
        assert "Generic error" in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_generate_image_success(self, async_client, mock_provider):
        """Test successful image generation."""
        result = await async_client.generate_image("Test prompt")

        assert result == ["url1"]
        mock_provider.generate_image.assert_called_once_with(
            "Test prompt", size="1024x1024", quality="standard", n=1
        )

    @pytest.mark.asyncio
    async def test_generate_image_with_options(self, async_client, mock_provider):
        """Test image generation with custom options."""
        result = await async_client.generate_image(
            "Test prompt",
            size="1792x1024",
            quality="hd",
            n=3
        )

        assert result == ["url1"]
        mock_provider.generate_image.assert_called_once_with(
            "Test prompt", size="1792x1024", quality="hd", n=3
        )

    @pytest.mark.asyncio
    async def test_generate_image_empty_prompt(self, async_client):
        """Test generate_image with empty prompt."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            await async_client.generate_image("")

    @pytest.mark.asyncio
    async def test_generate_image_invalid_n(self, async_client):
        """Test generate_image with invalid n parameter."""
        with pytest.raises(ValueError, match="n must be between 1 and 10"):
            await async_client.generate_image("Test", n=0)

        with pytest.raises(ValueError, match="n must be between 1 and 10"):
            await async_client.generate_image("Test", n=11)

    @pytest.mark.asyncio
    async def test_generate_image_provider_capability_error(self, async_client, mock_provider):
        """Test generate_image with provider capability error."""
        mock_provider.generate_image.side_effect = ProviderCapabilityError("generate_image", "TestProvider")

        with pytest.raises(ProviderCapabilityError):
            await async_client.generate_image("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_image_wrapped_exception(self, async_client, mock_provider):
        """Test generate_image wraps other exceptions."""
        mock_provider.generate_image.side_effect = Exception("Generic error")

        with pytest.raises(FileTransferError) as exc_info:
            await async_client.generate_image("Test prompt")

        assert "image generation" in str(exc_info.value)
        assert "Generic error" in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_path_conversion_in_upload_file(self, async_client, mock_provider):
        """Test that string paths are converted to Path objects."""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path_str = temp_file.name

            await async_client.upload_file(temp_path_str)

            # Should have converted string to Path
            mock_provider.upload_file.assert_called_once()
            call_args = mock_provider.upload_file.call_args[0]
            assert isinstance(call_args[0], Path)

    @pytest.mark.asyncio
    async def test_path_conversion_in_download_file(self, async_client, mock_provider):
        """Test that string paths are converted to Path objects in download."""
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path_str = f"{temp_dir}/downloaded.txt"

            result = await async_client.download_file("file_123", to_path=target_path_str)

            assert isinstance(result, Path)
            assert result.exists()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_isolation(self):
        """Test that concurrent requests don't interfere with each other."""
        mock_provider = AsyncMock()

        # Different responses for different prompts
        async def mock_ask(prompt, **kwargs):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"Response for {prompt}"

        mock_provider.ask.side_effect = mock_ask

        client = AsyncAiClient(provider=mock_provider)

        # Make concurrent requests
        prompts = [f"Prompt {i}" for i in range(10)]
        results = await client.ask_many(prompts, concurrency=5)

        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.response == f"Response for Prompt {i}"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_large_number_of_prompts(self):
        """Test handling large numbers of prompts."""
        mock_provider = AsyncMock()
        mock_provider.ask.return_value = "Response"

        client = AsyncAiClient(provider=mock_provider)

        # Test with 100 prompts
        prompts = [f"Prompt {i}" for i in range(100)]
        results = await client.ask_many(prompts, concurrency=10)

        assert len(results) == 100
        assert all(r.error is None for r in results)
        assert mock_provider.ask.call_count == 100

    @pytest.mark.asyncio
    async def test_exception_during_task_creation(self):
        """Test handling of exceptions during task creation."""
        mock_provider: AsyncMock = AsyncMock()
        client: AsyncAiClient = AsyncAiClient(provider=mock_provider)

        created_coroutines: list[object] = []

        def mock_create_task(coro: object) -> None:
            created_coroutines.append(coro)
            raise RuntimeError("Task creation failed")

        try:
            # IMPORTANT: patch the create_task used by ai_utilities.async_client
            with patch("ai_utilities.async_client.asyncio.create_task", side_effect=mock_create_task):
                with pytest.raises(RuntimeError, match="Task creation failed"):
                    await client.ask_many(["Test prompt"])
        finally:
            for coro in created_coroutines:
                try:
                    coro.close()  # type: ignore[attr-defined]
                except Exception:
                    pass
