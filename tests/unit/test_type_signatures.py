"""Tests for correct type signatures and parameter filtering."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings, AsyncAiClient
from tests.fake_provider import FakeProvider


class TestTypeSignatures:
    """Test that methods return correct types as documented."""
    
    def test_ask_returns_str_for_text_format(self):
        """Test ask() returns string for text format."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        response = client.ask("test prompt", return_format="text")
        assert isinstance(response, str)
        assert "fake response" in response
    
    def test_ask_returns_dict_for_json_format(self):
        """Test ask() returns dict for JSON format."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        response = client.ask("test prompt", return_format="json")
        assert isinstance(response, dict)
        assert "answer" in response
        assert isinstance(response["answer"], str)
    
    def test_ask_returns_list_for_multiple_prompts_text(self):
        """Test ask() returns list of strings for multiple prompts with text format."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        prompts = ["prompt 1", "prompt 2", "prompt 3"]
        responses = client.ask(prompts, return_format="text")
        
        assert isinstance(responses, list)
        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, str)
    
    def test_ask_returns_list_for_multiple_prompts_json(self):
        """Test ask() returns list of dicts for multiple prompts with JSON format."""
        fake_provider = FakeProvider()
        client = AiClient(provider=fake_provider)
        
        prompts = ["prompt 1", "prompt 2", "prompt 3"]
        responses = client.ask(prompts, return_format="json")
        
        assert isinstance(responses, list)
        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, dict)
            assert "answer" in response
    
    def test_ask_json_returns_dict_or_list(self):
        """Test ask_json() returns dict or list."""
        fake_provider = FakeProvider(['{"test": "data"}'])
        client = AiClient(provider=fake_provider)
        
        response = client.ask_json("test prompt")
        assert isinstance(response, (dict, list))
        if isinstance(response, dict):
            assert "test" in response


class TestParameterFiltering:
    """Test that internal fields are not passed to providers."""
    
    def test_internal_fields_excluded_from_provider_kwargs(self):
        """Test that api_key and internal fields are excluded from provider kwargs."""
        fake_provider = FakeProvider()
        settings = AiSettings(
            api_key="secret-key",
            model="test-model-1",
            temperature=0.5,
            max_tokens=100,
            usage_scope="per_client",
            usage_client_id="test-client",
            update_check_days=15
        )
        client = AiClient(settings=settings, provider=fake_provider)
        
        # Make a request
        client.ask("test prompt")
        
        # Check what was passed to provider
        kwargs = fake_provider.last_kwargs
        
        # Should include runtime parameters
        assert "model" in kwargs
        assert "temperature" in kwargs
        assert "max_tokens" in kwargs
        assert kwargs["model"] == "test-model-1"
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100
        
        # Should NOT include internal fields
        assert "api_key" not in kwargs
        assert "usage_scope" not in kwargs
        assert "usage_client_id" not in kwargs
        assert "update_check_days" not in kwargs
    
    def test_user_kwargs_override_settings(self):
        """Test that user kwargs properly override settings."""
        fake_provider = FakeProvider()
        settings = AiSettings(
            api_key="secret-key",
            model="default-model",
            temperature=0.7,
            max_tokens=200
        )
        client = AiClient(settings=settings, provider=fake_provider)
        
        # Make request with overrides
        client.ask(
            "test prompt", 
            model="override-model", 
            temperature=0.3, 
            max_tokens=150
        )
        
        # Check what was passed to provider
        kwargs = fake_provider.last_kwargs
        
        # Should use user overrides
        assert kwargs["model"] == "override-model"
        assert kwargs["temperature"] == 0.3
        assert kwargs["max_tokens"] == 150
        
        # Should still not include internal fields
        assert "api_key" not in kwargs
    
    def test_none_values_excluded(self):
        """Test that None values are excluded from provider kwargs."""
        fake_provider = FakeProvider()
        settings = AiSettings(
            api_key="secret-key",
            model="test-model-1",
            temperature=0.5,
            max_tokens=None,  # This should be excluded
            base_url=None     # This should be excluded
        )
        client = AiClient(settings=settings, provider=fake_provider)
        
        # Make a request
        client.ask("test prompt")
        
        # Check what was passed to provider
        kwargs = fake_provider.last_kwargs
        
        # Should include non-None values
        assert "model" in kwargs
        assert "temperature" in kwargs
        
        # Should exclude None values
        assert "max_tokens" not in kwargs
        assert "base_url" not in kwargs


class TestAsyncTypeSignatures:
    """Test that async methods have correct type signatures."""
    
    @pytest.mark.asyncio
    async def test_async_ask_returns_str_for_text_format(self):
        """Test async ask() returns string for text format."""
        from ai_utilities.async_client import AsyncOpenAIProvider
        
        fake_provider = FakeProvider()
        async_provider = AsyncOpenAIProvider(AiSettings(api_key="test", model="test"))
        # Replace the internal sync provider with our fake one for testing
        async_provider._sync_provider = fake_provider
        
        client = AsyncAiClient(provider=async_provider)
        
        response = await client.ask("test prompt", return_format="text")
        assert isinstance(response, str)
        assert "fake response" in response
    
    @pytest.mark.asyncio
    async def test_async_ask_returns_dict_for_json_format(self):
        """Test async ask() returns dict for JSON format."""
        from ai_utilities.async_client import AsyncOpenAIProvider
        
        fake_provider = FakeProvider()
        async_provider = AsyncOpenAIProvider(AiSettings(api_key="test", model="test"))
        # Replace the internal sync provider with our fake one for testing
        async_provider._sync_provider = fake_provider
        
        client = AsyncAiClient(provider=async_provider)
        
        response = await client.ask("test prompt", return_format="json")
        assert isinstance(response, dict)
        assert "answer" in response
        assert isinstance(response["answer"], str)
