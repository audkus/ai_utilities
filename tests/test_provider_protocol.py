"""Comprehensive tests for the new provider protocol."""

import asyncio
import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities import AiClient, AiSettings
from ai_utilities.env_overrides import override_env
from tests.fake_provider import FakeProvider


class TestProviderProtocol:
    """Test the new provider protocol with return_format support."""
    
    def test_fake_provider_text_format(self):
        """Test fake provider returns string for text format."""
        provider = FakeProvider()
        
        response = provider.ask("test prompt", return_format="text")
        
        assert isinstance(response, str)
        assert "test prompt" in response
    
    def test_fake_provider_json_format(self):
        """Test fake provider returns dict for json format."""
        provider = FakeProvider()
        
        response = provider.ask("test prompt", return_format="json")
        
        assert isinstance(response, dict)
        assert "answer" in response
        assert "test prompt" in response["answer"]
    
    def test_fake_provider_many_text_format(self):
        """Test fake provider ask_many returns strings for text format."""
        provider = FakeProvider()
        prompts = ["prompt1", "prompt2"]
        
        responses = provider.ask_many(prompts, return_format="text")
        
        assert isinstance(responses, list)
        assert len(responses) == 2
        assert all(isinstance(r, str) for r in responses)
        assert "prompt1" in responses[0]
        assert "prompt2" in responses[1]
    
    def test_fake_provider_many_json_format(self):
        """Test fake provider ask_many returns dicts for json format."""
        provider = FakeProvider()
        prompts = ["prompt1", "prompt2"]
        
        responses = provider.ask_many(prompts, return_format="json")
        
        assert isinstance(responses, list)
        assert len(responses) == 2
        assert all(isinstance(r, dict) for r in responses)
        assert all("answer" in r for r in responses)
    
    def test_kwargs_forwarding_fake_provider(self):
        """Test kwargs are forwarded to fake provider."""
        provider = FakeProvider()
        
        provider.ask("test", model="test-model-1", temperature=0.5, max_tokens=100)
        
        assert provider.last_kwargs["model"] == "test-model-1"
        assert provider.last_kwargs["temperature"] == 0.5
        assert provider.last_kwargs["max_tokens"] == 100
    
    def test_kwargs_forwarding_fake_provider_many(self):
        """Test kwargs are forwarded to fake provider ask_many."""
        provider = FakeProvider()
        prompts = ["test1", "test2"]
        
        provider.ask_many(prompts, model="test-model-2", temperature=0.7)
        
        assert provider.last_kwargs["model"] == "test-model-2"
        assert provider.last_kwargs["temperature"] == 0.7


class TestAiClientIntegration:
    """Test AiClient integration with new provider protocol."""
    
    def test_ai_client_text_format(self):
        """Test AiClient returns string for text format."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            provider = FakeProvider()
            client = AiClient(settings, provider=provider)
            
            response = client.ask("test prompt", return_format="text")
            
            assert isinstance(response, str)
            assert "test prompt" in response
    
    def test_ai_client_json_format(self):
        """Test AiClient returns dict for json format."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            provider = FakeProvider()
            client = AiClient(settings, provider=provider)
            
            response = client.ask("test prompt", return_format="json")
            
            assert isinstance(response, dict)
            assert "answer" in response
    
    def test_ai_client_many_json_format(self):
        """Test AiClient ask_many returns list of AskResult with dict responses."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            provider = FakeProvider()
            client = AiClient(settings, provider=provider)
            prompts = ["prompt1", "prompt2"]
            
            results = client.ask_many(prompts, return_format="json")
            
            assert isinstance(results, list)
            assert len(results) == 2
            for result in results:
                assert hasattr(result, 'response')
                assert hasattr(result, 'error')
                assert result.error is None
                assert isinstance(result.response, dict)
                assert "answer" in result.response
    
    def test_ai_client_kwargs_forwarding(self):
        """Test kwargs are forwarded through AiClient to provider."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            provider = FakeProvider()
            client = AiClient(settings, provider=provider)
            
            client.ask("test", model="test-model-1", temperature=0.5, max_tokens=100)
            
            assert provider.last_kwargs["model"] == "test-model-1"
            assert provider.last_kwargs["temperature"] == 0.5
            assert provider.last_kwargs["max_tokens"] == 100
    
    def test_ai_client_many_kwargs_forwarding(self):
        """Test kwargs are forwarded through AiClient ask_many to provider."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            provider = FakeProvider()
            client = AiClient(settings, provider=provider)
            prompts = ["test1", "test2"]
            
            client.ask_many(prompts, model="test-model-2", temperature=0.7)
            
            assert provider.last_kwargs["model"] == "test-model-2"
            assert provider.last_kwargs["temperature"] == 0.7


class TestRetryBehavior:
    """Test retry behavior differences between ask_many and ask_many_with_retry."""
    
    def test_ask_many_no_retry(self):
        """Test ask_many does not retry on failure."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            
            # Create a provider that fails on second call
            class FailingProvider(FakeProvider):
                def __init__(self):
                    super().__init__()
                    self.fail_count = 0
                    self.call_log = []
                
                def ask(self, prompt, *, return_format="text", **kwargs):
                    self.fail_count += 1
                    self.call_log.append(f"Call {self.fail_count}: {prompt}")
                    if self.fail_count == 2:
                        raise ValueError("Simulated failure")
                    # Don't call super() to avoid double counting
                    response = self.responses[(self.fail_count - 1) % len(self.responses)]
                    formatted_response = response.format(prompt=prompt)
                    return formatted_response
            
            provider = FailingProvider()
            client = AiClient(settings, provider=provider)
            prompts = ["prompt1", "prompt2", "prompt3"]
            
            results = client.ask_many(prompts)
            
            # Should have attempted all prompts despite failure
            assert provider.fail_count == 3
            assert len(results) == 3
            assert results[0].error is None
            assert results[1].error is not None
            assert results[2].error is None
    
    def test_ask_many_with_retry_retries(self):
        """Test ask_many_with_retry retries on failure."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            
            # Create a provider that fails then succeeds
            class RetryProvider(FakeProvider):
                def __init__(self):
                    super().__init__()
                    self.fail_count = 0
                
                def ask(self, prompt, *, return_format="text", **kwargs):
                    self.fail_count += 1
                    if self.fail_count <= 2:  # Fail first 2 attempts
                        raise ValueError("Simulated failure")
                    # Don't call super() to avoid double counting
                    response = self.responses[(self.fail_count - 1) % len(self.responses)]
                    formatted_response = response.format(prompt=prompt)
                    return formatted_response
            
            provider = RetryProvider()
            client = AiClient(settings, provider=provider)
            prompts = ["prompt1"]
            
            results = client.ask_many_with_retry(prompts, max_retries=3)
            
            # Should have retried and succeeded
            assert provider.fail_count == 3  # 1 initial + 2 retries
            assert len(results) == 1
            assert results[0].error is None


class TestConcurrencyValidation:
    """Test concurrency parameter validation."""
    
    def test_invalid_concurrency_zero(self):
        """Test concurrency <= 0 raises ValueError."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            provider = FakeProvider()
            client = AiClient(settings, provider=provider)
            prompts = ["prompt1", "prompt2"]
            
            with pytest.raises(ValueError, match="concurrency must be >= 1"):
                client.ask_many(prompts, concurrency=0)
            
            with pytest.raises(ValueError, match="concurrency must be >= 1"):
                client.ask_many(prompts, concurrency=-1)


@pytest.mark.asyncio
class TestAsyncProviderProtocol:
    """Test async provider protocol."""
    
    async def test_async_client_json_format(self):
        """Test async client returns dict for json format."""
        from ai_utilities.async_client import AsyncAiClient
        
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            async_client = AsyncAiClient(settings)
            
            # Mock the async provider to return predictable response
            class MockAsyncProvider:
                async def ask(self, prompt, *, return_format="text", **kwargs):
                    if return_format == "json":
                        return {"answer": f"Async response to: {prompt}"}
                    return f"Async response to: {prompt}"
            
            async_client.provider = MockAsyncProvider()
            
            response = await async_client.ask("test prompt", return_format="json")
            
            assert isinstance(response, dict)
            assert "answer" in response
            assert "test prompt" in response["answer"]
    
    async def test_async_client_kwargs_forwarding(self):
        """Test async client forwards kwargs to provider."""
        from ai_utilities.async_client import AsyncAiClient
        
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            async_client = AsyncAiClient(settings)
            
            # Mock provider to capture kwargs
            received_kwargs = {}
            
            class MockAsyncProvider:
                async def ask(self, prompt, *, return_format="text", **kwargs):
                    nonlocal received_kwargs
                    received_kwargs = kwargs
                    return "response"
            
            async_client.provider = MockAsyncProvider()
            
            await async_client.ask("test", model="test-model-1", temperature=0.5)
            
            assert received_kwargs["model"] == "test-model-1"
            assert received_kwargs["temperature"] == 0.5


@pytest.mark.asyncio
class TestCancellationFriendliness:
    """Test cancellation friendliness of async operations."""
    
    async def test_cancellation_stops_background_tasks(self):
        """Test cancelling ask_many stops background tasks."""
        from ai_utilities.async_client import AsyncAiClient
        
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            async_client = AsyncAiClient(settings)
            
            # Create a slow provider
            class SlowAsyncProvider:
                def __init__(self):
                    self.calls_made = 0
                
                async def ask(self, prompt, *, return_format="text", **kwargs):
                    self.calls_made += 1
                    await asyncio.sleep(0.1)  # Simulate slow operation
                    return f"Response to: {prompt}"
            
            provider = SlowAsyncProvider()
            async_client.provider = provider
            
            # Start task with many prompts
            prompts = [f"prompt{i}" for i in range(10)]
            task = asyncio.create_task(
                async_client.ask_many(prompts, concurrency=5)
            )
            
            # Let it start a few operations
            await asyncio.sleep(0.05)
            
            # Cancel the task
            task.cancel()
            
            # Should raise CancelledError
            with pytest.raises(asyncio.CancelledError):
                await task
            
            # Verify not all prompts were processed
            assert provider.calls_made < 10
            
            # Give a moment for any cleanup
            await asyncio.sleep(0.01)
            
            # Verify no pending tasks (this is harder to test directly, but we can 
            # check that the provider wasn't called more after cancellation)
            initial_calls = provider.calls_made
            await asyncio.sleep(0.1)
            assert provider.calls_made == initial_calls


class TestFailFastCorrectness:
    """Test fail-fast behavior correctness."""
    
    def test_fail_fast_stops_remaining_prompts(self):
        """Test that after first failure, remaining prompts are not started."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            
            # Provider that tracks which prompts were attempted
            class TrackingProvider(FakeProvider):
                def __init__(self):
                    super().__init__()
                    self.attempted_prompts = []
                
                def ask(self, prompt, *, return_format="text", **kwargs):
                    self.attempted_prompts.append(prompt)
                    if "fail" in prompt:
                        raise ValueError("Simulated failure")
                    return super().ask(prompt, return_format=return_format, **kwargs)
            
            provider = TrackingProvider()
            client = AiClient(settings, provider=provider)
            
            # Prompts with one that will fail
            prompts = ["prompt1", "fail_prompt", "prompt3", "prompt4"]
            
            results = client.ask_many(prompts, fail_fast=True)
            
            # Should have stopped after the failure
            assert "prompt1" in provider.attempted_prompts
            assert "fail_prompt" in provider.attempted_prompts
            # prompt3 and prompt4 should not have been attempted
            assert "prompt3" not in provider.attempted_prompts
            assert "prompt4" not in provider.attempted_prompts
            
            # Results should reflect the failure
            assert len(results) == 4
            assert results[0].error is None  # prompt1 succeeded
            assert results[1].error is not None  # fail_prompt failed
            assert results[2].error is not None  # prompt3 marked as failed
            assert results[3].error is not None  # prompt4 marked as failed


class TestPartialFailure:
    """Test partial failure handling."""
    
    def test_ask_many_partial_failure(self):
        """Test ask_many handles partial failures correctly."""
        with override_env({"AI_API_KEY": "test-key"}):
            settings = AiSettings()
            
            # Provider that fails on specific prompts
            class PartialFailureProvider(FakeProvider):
                def ask(self, prompt, *, return_format="text", **kwargs):
                    if "fail" in prompt:
                        raise ValueError("Simulated failure for: " + prompt)
                    return super().ask(prompt, return_format=return_format, **kwargs)
            
            provider = PartialFailureProvider()
            client = AiClient(settings, provider=provider)
            
            prompts = ["success1", "fail_prompt", "success2", "fail_prompt2"]
            
            results = client.ask_many(prompts)
            
            # List length should match prompts
            assert len(results) == 4
            
            # Check individual results
            assert results[0].error is None
            assert results[0].response is not None
            assert "success1" in results[0].response
            
            assert results[1].error is not None
            assert results[1].response is None
            assert "fail_prompt" in str(results[1].error)
            
            assert results[2].error is None
            assert results[2].response is not None
            assert "success2" in results[2].response
            
            assert results[3].error is not None
            assert results[3].response is None
            
            # Function should not raise
            # (If we get here, the test passes)


class TestEnvironmentIsolation:
    """Test that provider tests use proper environment isolation."""
    
    def test_os_environ_unchanged_with_override_env(self):
        """Test that override_env doesn't change os.environ."""
        original_env = dict(os.environ)
        
        with override_env({"AI_API_KEY": "test-key", "AI_MODEL": "test-model-1"}):
            # os.environ should be unchanged
            assert os.environ == original_env
            
            # But client should use the overrides
            settings = AiSettings()
            assert settings.api_key == "test-key"
            assert settings.model == "test-model-1"
        
        # Environment should be exactly as it was
        assert os.environ == original_env
