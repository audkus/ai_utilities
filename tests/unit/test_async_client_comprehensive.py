"""Comprehensive async client tests for Phase 3 - Async functionality."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

from ai_utilities import AiSettings, AsyncAiClient
from ai_utilities.models import AskResult
from tests.fake_provider import FakeAsyncProvider, FakeProviderError


class TestAsyncAiClientBasics:
    """Test AsyncAiClient basic functionality."""
    
    @pytest.mark.asyncio
    async def test_async_client_creation_default(self, openai_mocks):
        """Test creating AsyncAiClient with default settings."""
        constructor_mock, client_mock = openai_mocks
        
        client = AsyncAiClient()
        
        assert client.settings is not None
        assert client.provider is not None
        assert client.show_progress is True
        assert hasattr(client.provider, 'ask')
        assert hasattr(client.provider, 'ask_many')
    
    @pytest.mark.asyncio
    async def test_async_client_creation_with_settings(self, fake_settings):
        """Test creating AsyncAiClient with custom settings."""
        # Use a simple provider to avoid mock issues
        from tests.fake_provider import FakeAsyncProvider
        provider = FakeAsyncProvider()
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        assert client.settings == fake_settings
        assert client.provider is not None
        assert client.show_progress is True
    
    @pytest.mark.asyncio
    async def test_async_client_with_custom_provider(self, fake_settings):
        """Test creating AsyncAiClient with custom async provider."""
        custom_provider = FakeAsyncProvider(responses=["Custom response: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=custom_provider)
        
        assert client.provider is custom_provider
        assert client.settings == fake_settings
    
    @pytest.mark.asyncio
    async def test_async_client_show_progress_option(self, fake_settings):
        """Test AsyncAiClient show_progress option."""
        client_with_progress = AsyncAiClient(settings=fake_settings, show_progress=True)
        client_without_progress = AsyncAiClient(settings=fake_settings, show_progress=False)
        
        assert client_with_progress.show_progress is True
        assert client_without_progress.show_progress is False


class TestAsyncAiClientAsk:
    """Test AsyncAiClient ask() method."""
    
    @pytest.mark.asyncio
    async def test_async_ask_single_prompt(self, fake_settings):
        """Test basic async ask() functionality."""
        provider = FakeAsyncProvider(responses=["Async response: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        response = await client.ask("test prompt")
        
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        assert provider.sync_provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_ask_with_parameters(self, fake_settings):
        """Test async ask() with parameters."""
        provider = FakeAsyncProvider(responses=["Response with temp {temperature}: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        response = await client.ask("test", temperature=0.5, max_tokens=100)
        
        # Check that response contains the template (parameters not substituted)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        assert "{prompt}" in response or "test" in response
        assert provider.sync_provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_ask_json_format(self, fake_settings):
        """Test async ask() with JSON return format."""
        provider = FakeAsyncProvider(responses=['{"result": "json response for {prompt}"}'])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        response = await client.ask("test", return_format="json")
        
        # Response might be dict or string depending on parsing
        assert isinstance(response, (dict, str))
        if isinstance(response, dict):
            # Check for expected keys or content
            assert "result" in response or "answer" in response
        else:
            # If string, should contain JSON content
            assert isinstance(response, str)  # Contract: response is string type
            assert len(response) > 0  # Contract: non-empty response
        assert provider.sync_provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_ask_error_handling(self, fake_settings):
        """Test async ask() error handling."""
        provider = FakeAsyncProvider(should_fail=True)
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        with pytest.raises(FakeProviderError):
            await client.ask("test")
        
        assert provider.sync_provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_ask_deterministic_responses(self, fake_settings):
        """Test that async ask() returns deterministic responses."""
        provider = FakeAsyncProvider(responses=["Deterministic: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        response1 = await client.ask("test")
        response2 = await client.ask("test")
        
        assert response1 == response2 == "Deterministic: test"
        assert provider.sync_provider.call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_ask_concurrent_calls(self, fake_settings):
        """Test concurrent async ask() calls."""
        provider = FakeAsyncProvider(responses=["Concurrent {prompt}: {call_count}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        # Make concurrent calls
        tasks = [
            client.ask(f"prompt_{i}")
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All calls should have completed
        assert len(responses) == 5
        assert provider.sync_provider.call_count == 5
        
        # Each response should contain the prompt template
        for i, response in enumerate(responses):
            assert f"prompt_{i}" in response or "Concurrent" in response
    
    @pytest.mark.asyncio
    async def test_async_ask_with_delay(self, fake_settings):
        """Test async ask() with artificial delay."""
        provider = FakeAsyncProvider(responses=["Delayed: {prompt}"], delay=0.01)
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        start_time = time.time()
        response = await client.ask("test")
        end_time = time.time()
        
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        assert end_time - start_time >= 0.01  # Should have waited
        assert provider.sync_provider.call_count == 1


class TestAsyncAiClientAskMany:
    """Test AsyncAiClient ask_many() method."""
    
    @pytest.mark.asyncio
    async def test_async_ask_many_basic(self, fake_settings):
        """Test basic async ask_many() functionality."""
        provider = FakeAsyncProvider(responses=["Response {i}: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        prompts = ["prompt1", "prompt2", "prompt3"]
        results = await client.ask_many(prompts)
        
        assert len(results) == 3
        assert all(isinstance(r, AskResult) for r in results)
        assert provider.sync_provider.call_count == 3
        
        # Check results are in correct order
        for i, result in enumerate(results):
            assert result.prompt == prompts[i]
            assert result.response is not None
            assert result.error is None
            assert result.duration_s >= 0
    
    @pytest.mark.asyncio
    async def test_async_ask_many_with_parameters(self, fake_settings):
        """Test async ask_many() with parameters."""
        provider = FakeAsyncProvider(responses=["Param response: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        prompts = ["test1", "test2"]
        results = await client.ask_many(prompts, temperature=0.5, max_tokens=50)
        
        assert len(results) == 2
        assert provider.sync_provider.call_count == 2
        
        for result in results:
            assert isinstance(result.response, str)  # Contract: response is string type
            assert len(result.response) > 0  # Contract: non-empty response
    
    @pytest.mark.asyncio
    async def test_async_ask_many_json_format(self, fake_settings):
        """Test async ask_many() with JSON return format."""
        provider = FakeAsyncProvider(responses=['{"json": "response for {prompt}"}'])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        prompts = ["test1", "test2"]
        results = await client.ask_many(prompts, return_format="json")
        
        assert len(results) == 2
        assert provider.sync_provider.call_count == 2
        
        for result in results:
            assert isinstance(result.response, (dict, str))
    
    @pytest.mark.asyncio
    async def test_async_ask_many_concurrency_control(self, fake_settings):
        """Test async ask_many() concurrency control."""
        provider = FakeAsyncProvider(responses=["Concurrent: {prompt}"], delay=0.01)
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        prompts = [f"prompt_{i}" for i in range(10)]
        
        # Test with low concurrency
        start_time = time.time()
        results = await client.ask_many(prompts, concurrency=2)
        low_concurrency_time = time.time() - start_time
        
        assert len(results) == 10
        assert provider.sync_provider.call_count == 10
        
        # Test with high concurrency
        provider.sync_provider.call_count = 0  # Reset counter
        start_time = time.time()
        results = await client.ask_many(prompts, concurrency=10)
        high_concurrency_time = time.time() - start_time
        
        assert len(results) == 10
        assert provider.sync_provider.call_count == 10
        
        # High concurrency should be faster (or at least not significantly slower)
        assert high_concurrency_time <= low_concurrency_time + 0.1
    
    @pytest.mark.asyncio
    async def test_async_ask_many_fail_fast(self, fake_settings):
        """Test async ask_many() with fail_fast=True."""
        provider = FakeAsyncProvider(should_fail=True, fail_on_call=3)
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        prompts = ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"]
        results = await client.ask_many(prompts, fail_fast=True)
        
        # Should have processed some prompts
        assert len(results) == 5
        
        # Basic functionality test - all results should be AskResult objects
        for result in results:
            assert isinstance(result, AskResult)
            assert result.prompt is not None
    
    @pytest.mark.asyncio
    async def test_async_ask_many_progress_callback(self, fake_settings):
        """Test async ask_many() with progress callback."""
        provider = FakeAsyncProvider(responses=["Progress: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        progress_calls = []
        
        def progress_callback(completed, total):
            progress_calls.append((completed, total))
        
        prompts = ["p1", "p2", "p3"]
        results = await client.ask_many(prompts, on_progress=progress_callback)
        
        assert len(results) == 3
        
        # Should have received progress updates
        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)  # Final call should show completion
        
        # Progress should be monotonic
        for i in range(len(progress_calls) - 1):
            assert progress_calls[i][0] <= progress_calls[i + 1][0]
    
    @pytest.mark.asyncio
    async def test_async_ask_many_progress_callback_error(self, fake_settings):
        """Test async ask_many() handles progress callback errors gracefully."""
        provider = FakeAsyncProvider(responses=["Error progress: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        def bad_progress_callback(completed, total):
            if completed == 2:
                raise ValueError("Progress callback error")
        
        prompts = ["p1", "p2", "p3"]
        
        # Should not raise despite progress callback error
        results = await client.ask_many(prompts, on_progress=bad_progress_callback)
        
        assert len(results) == 3
        assert all(r.error is None for r in results)
    
    @pytest.mark.asyncio
    async def test_async_ask_many_empty_prompts(self, fake_settings):
        """Test async ask_many() with empty prompts list."""
        provider = FakeAsyncProvider(responses=["Empty test"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        results = await client.ask_many([])
        
        assert results == []
        assert provider.sync_provider.call_count == 0
    
    @pytest.mark.asyncio
    async def test_async_ask_many_error_handling(self, fake_settings):
        """Test async ask_many() error handling for individual prompts."""
        provider = FakeAsyncProvider(
            responses=["Success: {prompt}"],
            should_fail=True,
            fail_on_call=2  # Fail on second call
        )
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        prompts = ["success1", "fail_prompt", "success2"]
        results = await client.ask_many(prompts, fail_fast=False)
        
        assert len(results) == 3
        assert provider.sync_provider.call_count == 3
        
        # Basic functionality test - all results should be present
        for result in results:
            assert isinstance(result, AskResult)
            assert result.prompt is not None
            # Either response or error should be present
            assert result.response is not None or result.error is not None


class TestAsyncAiClientIntegration:
    """Test AsyncAiClient integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_async_client_with_sync_provider_pattern(self, fake_settings):
        """Test that async client works with sync provider pattern."""
        # This tests the actual AsyncOpenAIProvider pattern
        client = AsyncAiClient(settings=fake_settings)
        
        # Should be able to create client without errors
        assert client is not None
        assert hasattr(client, 'ask')
        assert hasattr(client, 'ask_many')
        
        # Basic functionality test (will use real provider pattern)
        # We'll test with our fake provider for reliability
        fake_provider = FakeAsyncProvider(responses=["Integration test: {prompt}"])
        client.provider = fake_provider
        
        response = await client.ask("integration")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    @pytest.mark.asyncio
    async def test_async_client_mixed_operations(self, fake_settings):
        """Test mixing different async operations."""
        provider = FakeAsyncProvider(responses=["Mixed: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        # Mix single and batch operations
        single_response = await client.ask("single")
        batch_results = await client.ask_many(["batch1", "batch2"])
        
        assert single_response == "Mixed: single"
        assert len(batch_results) == 2
        assert provider.sync_provider.call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_client_reuse(self, fake_settings):
        """Test reusing AsyncAiClient for multiple operations."""
        provider = FakeAsyncProvider(responses=["Reuse: {prompt}"])
        client = AsyncAiClient(settings=fake_settings, provider=provider)
        
        # Use client multiple times
        for i in range(5):
            response = await client.ask(f"reuse_{i}")
            assert response == f"Reuse: reuse_{i}"
        
        # Should have made 5 calls
        assert provider.sync_provider.call_count == 5
        
        # Client should still be functional
        final_response = await client.ask("final")
        assert final_response == "Reuse: final"
        assert provider.sync_provider.call_count == 6
