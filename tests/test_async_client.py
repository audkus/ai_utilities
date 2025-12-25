"""Tests for AsyncAiClient functionality."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from ai_utilities.async_client import AsyncAiClient, AsyncOpenAIProvider
from ai_utilities.client import AiSettings
from ai_utilities.models import AskResult


class TestAsyncAiClient:
    """Test AsyncAiClient functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock AI settings."""
        return AiSettings(
            api_key="test-key",
            model="test-model-1",
            temperature=0.7
        )
    
    @pytest.fixture
    def async_client(self, mock_settings):
        """Create AsyncAiClient instance for testing."""
        return AsyncAiClient(settings=mock_settings)
    
    @pytest.mark.asyncio
    async def test_ask_single_prompt(self, async_client):
        """Test asking a single prompt asynchronously."""
        with patch.object(async_client.provider, 'ask', new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = "Test response"
            
            result = await async_client.ask("What is AI?")
            
            assert result == "Test response"
            mock_ask.assert_called_once_with("What is AI?", return_format="text")
    
    @pytest.mark.asyncio
    async def test_ask_many_sequential_order(self, async_client):
        """Test that ask_many maintains sequential order."""
        prompts = ["prompt1", "prompt2", "prompt3"]
        responses = ["response1", "response2", "response3"]
        
        with patch.object(async_client.provider, 'ask', new_callable=AsyncMock) as mock_ask:
            # Configure mock to return responses in order
            mock_ask.side_effect = responses
            
            results = await async_client.ask_many(prompts, concurrency=1)
            
            assert len(results) == 3
            assert results[0].prompt == "prompt1"
            assert results[0].response == "response1"
            assert results[1].prompt == "prompt2"
            assert results[1].response == "response2"
            assert results[2].prompt == "prompt3"
            assert results[2].response == "response3"
    
    @pytest.mark.asyncio
    async def test_ask_many_concurrency_cap(self, async_client):
        """Test that concurrency is respected (max in-flight <= concurrency)."""
        prompts = [f"prompt{i}" for i in range(10)]
        concurrency = 3
        
        # Track concurrent calls
        concurrent_calls = 0
        max_concurrent = 0
        call_events = []
        
        async def mock_ask_with_delay(prompt: str, **kwargs):
            nonlocal concurrent_calls, max_concurrent
            concurrent_calls += 1
            max_concurrent = max(max_concurrent, concurrent_calls)
            call_events.append(concurrent_calls)
            
            # Simulate some work
            await asyncio.sleep(0.1)
            
            concurrent_calls -= 1
            return f"response for {prompt}"
        
        with patch.object(async_client.provider, 'ask', side_effect=mock_ask_with_delay):
            results = await async_client.ask_many(prompts, concurrency=concurrency)
        
        # Verify concurrency was respected
        assert max_concurrent <= concurrency
        assert len(results) == len(prompts)
        
        # Verify all results are successful
        for result in results:
            assert result.error is None
            assert result.response is not None
    
    @pytest.mark.asyncio
    async def test_ask_many_partial_failures_returned(self, async_client):
        """Test that partial failures are properly returned in results."""
        prompts = ["prompt1", "prompt2", "prompt3", "prompt4"]
        
        async def mock_ask_with_failures(prompt: str, **kwargs):
            if prompt == "prompt2":
                raise ValueError("Simulated error for prompt2")
            elif prompt == "prompt4":
                raise RuntimeError("Simulated error for prompt4")
            else:
                return f"response for {prompt}"
        
        with patch.object(async_client.provider, 'ask', side_effect=mock_ask_with_failures):
            results = await async_client.ask_many(prompts, concurrency=2)
        
        assert len(results) == 4
        
        # Check successful results
        assert results[0].error is None
        assert results[0].response == "response for prompt1"
        assert results[2].error is None
        assert results[2].response == "response for prompt3"
        
        # Check failed results
        assert results[1].error is not None
        assert "Simulated error for prompt2" in results[1].error
        assert results[1].response is None
        
        assert results[3].error is not None
        assert "Simulated error for prompt4" in results[3].error
        assert results[3].response is None
    
    @pytest.mark.asyncio
    async def test_ask_many_fail_fast_cancels_remaining(self, async_client):
        """Test that fail_fast=True cancels remaining tasks on first failure."""
        prompts = ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"]
        
        # Track which prompts were processed
        processed_prompts = []
        
        async def mock_ask_with_tracking(prompt: str, **kwargs):
            processed_prompts.append(prompt)
            if prompt == "prompt3":
                raise ValueError("First error")
            await asyncio.sleep(0.1)  # Simulate work
            return f"response for {prompt}"
        
        with patch.object(async_client.provider, 'ask', side_effect=mock_ask_with_tracking):
            results = await async_client.ask_many(prompts, concurrency=3, fail_fast=True)
        
        # Should have processed some prompts but not all
        assert len(processed_prompts) <= len(prompts)
        
        # Results should contain some successes and some failures/cancellations
        assert len(results) == len(prompts)
        
        # At least one result should have an error
        error_results = [r for r in results if r.error is not None]
        assert len(error_results) > 0
    
    @pytest.mark.asyncio
    async def test_ask_many_with_retry_success(self, async_client):
        """Test that retry logic succeeds after transient failures."""
        prompts = ["prompt1", "prompt2", "prompt3"]
        
        # Track call counts for each prompt
        call_counts = {"prompt1": 0, "prompt2": 0, "prompt3": 0}
        
        async def mock_ask_with_retry(prompt: str, **kwargs):
            call_counts[prompt] += 1
            
            if prompt == "prompt2" and call_counts[prompt] == 1:
                # Fail on first attempt with retryable error
                raise Exception("Rate limit exceeded")
            
            await asyncio.sleep(0.05)
            return f"response for {prompt}"
        
        with patch.object(async_client.provider, 'ask', side_effect=mock_ask_with_retry):
            results = await async_client.ask_many_with_retry(
                prompts, 
                concurrency=2, 
                max_retries=2
            )
        
        # All should succeed eventually
        assert len(results) == 3
        for result in results:
            assert result.error is None
            assert result.response is not None
        
        # prompt2 should have been called twice (original + retry)
        assert call_counts["prompt1"] == 1
        assert call_counts["prompt2"] == 2
        assert call_counts["prompt3"] == 1
    
    @pytest.mark.asyncio
    async def test_ask_many_with_retry_max_attempts(self, async_client):
        """Test that retry logic stops after max attempts."""
        prompts = ["prompt1"]
        
        async def mock_ask_always_fails(prompt: str, **kwargs):
            raise Exception("Persistent error")
        
        with patch.object(async_client.provider, 'ask', side_effect=mock_ask_always_fails):
            results = await async_client.ask_many_with_retry(
                prompts, 
                concurrency=1, 
                max_retries=2
            )
        
        assert len(results) == 1
        assert results[0].error is not None
        assert "Max retries exceeded" in results[0].error or "Persistent error" in results[0].error
    
    @pytest.mark.asyncio
    async def test_ask_many_progress_callback(self, async_client):
        """Test that progress callback is called correctly."""
        prompts = ["prompt1", "prompt2", "prompt3"]
        progress_calls = []
        
        def progress_callback(completed: int, total: int):
            progress_calls.append((completed, total))
        
        async def mock_ask_with_delay(prompt: str, **kwargs):
            await asyncio.sleep(0.1)
            return f"response for {prompt}"
        
        with patch.object(async_client.provider, 'ask', side_effect=mock_ask_with_delay):
            results = await async_client.ask_many(
                prompts, 
                concurrency=2, 
                on_progress=progress_callback
            )
        
        # Progress should be reported for each completion
        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3)
        assert progress_calls[1] == (2, 3)
        assert progress_calls[2] == (3, 3)
    
    @pytest.mark.asyncio
    async def test_ask_many_empty_prompts(self, async_client):
        """Test handling of empty prompts list."""
        results = await async_client.ask_many([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_ask_result_fields(self, async_client):
        """Test that AskResult contains all required fields."""
        with patch.object(async_client.provider, 'ask', new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = "Test response"
            
            start_time = time.time()
            results = await async_client.ask_many(["test prompt"])
            end_time = time.time()
            
            result = results[0]
            
            # Required fields
            assert result.prompt == "test prompt"
            assert result.response == "Test response"
            assert result.error is None
            assert isinstance(result.duration_s, float)
            assert result.duration_s > 0
            assert result.duration_s < (end_time - start_time + 0.1)  # Allow some tolerance
            
            # Optional fields
            assert result.model == "test-model-1"
            assert result.tokens_used is None  # Not implemented yet


class TestAsyncOpenAIProvider:
    """Test AsyncOpenAIProvider implementation."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock AI settings."""
        return AiSettings(api_key="test-key", model="test-model-1")
    
    @pytest.fixture
    def async_provider(self, mock_settings):
        """Create AsyncOpenAIProvider instance for testing."""
        return AsyncOpenAIProvider(mock_settings)
    
    @pytest.mark.asyncio
    async def test_async_provider_uses_sync_provider(self, async_provider):
        """Test that AsyncOpenAIProvider delegates to sync provider."""
        with patch.object(async_provider._sync_provider, 'ask') as mock_sync_ask:
            mock_sync_ask.return_value = "sync response"
            
            result = await async_provider.ask("test prompt", return_format="text")
            
            assert result == "sync response"
            mock_sync_ask.assert_called_once_with("test prompt", return_format="text")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
