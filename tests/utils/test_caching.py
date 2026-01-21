"""
Tests for smart caching functionality.

Tests caching behavior with deterministic fake providers to ensure
no real API calls are made and tests run quickly and reliably.
"""

import time
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from ai_utilities.cache import MemoryCache, NullCache, stable_hash
from ai_utilities.client import AiClient, AiSettings
from ai_utilities.json_parsing import JsonParseError
from ai_utilities.providers.base_provider import BaseProvider


class FakeProvider(BaseProvider):
    """Fake provider for testing caching behavior.
    
    Counts method calls and returns deterministic outputs.
    """
    
    def __init__(self, settings: AiSettings):
        self.settings = settings
        self.ask_count = 0
        self.ask_text_count = 0
        self.ask_many_count = 0
        self.responses = {}
        self.default_response = "Default response"
    
    def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Any:
        """Fake ask method that counts calls and returns deterministic responses."""
        self.ask_count += 1
        
        # Generate deterministic response based on prompt and params
        key = stable_hash({"prompt": prompt, "return_format": return_format, "params": kwargs})
        
        if key in self.responses:
            return self.responses[key]
        
        # Default deterministic responses
        if return_format == "json":
            return {"result": f"Response to: {prompt}", "model": kwargs.get("model", "default")}
        else:
            return f"Response to: {prompt} (model: {kwargs.get('model', 'default')})"
    
    def ask_text(self, prompt: str, **kwargs) -> str:
        """Fake ask_text method for JSON parsing tests."""
        self.ask_text_count += 1
        
        key = stable_hash({"prompt": prompt, "params": kwargs})
        
        if key in self.responses:
            return self.responses[key]
        
        # Return JSON string for JSON parsing tests
        if "json" in prompt.lower():
            return '{"result": "parsed data", "value": 42}'
        else:
            return f"Text response to: {prompt}"
    
    def ask_many(self, prompts: List[str], *, return_format: str = "text", **kwargs) -> List[Any]:
        """Fake ask_many method."""
        self.ask_many_count += 1
        return [self.ask(prompt, return_format=return_format, **kwargs) for prompt in prompts]
    
    def upload_file(self, path, *, purpose="assistants", filename=None, mime_type=None):
        """Fake upload_file method."""
        return {"id": "fake-file-id", "filename": filename or "fake.txt"}
    
    def download_file(self, file_id):
        """Fake download_file method."""
        return b"fake file content"
    
    def generate_image(self, prompt, *, size="1024x1024", quality="standard", n=1):
        """Fake generate_image method."""
        return [{"url": f"https://fake.com/image-{i}.png"} for i in range(n)]
    
    def set_response(self, prompt: str, response: Any, return_format: str = "text", **kwargs):
        """Set a specific response for a given prompt and parameters."""
        key = stable_hash({"prompt": prompt, "return_format": return_format, "params": kwargs})
        self.responses[key] = response


class TestCachingBasics:
    """Test basic caching functionality."""
    
    def test_null_cache_always_misses(self):
        """Test that NullCache never returns cached values."""
        cache = NullCache()
        
        assert cache.get("key") is None
        cache.set("key", "value")
        assert cache.get("key") is None
    
    def test_memory_cache_basic_operations(self):
        """Test MemoryCache basic get/set operations."""
        cache = MemoryCache()
        
        # Initially empty
        assert cache.get("key") is None
        
        # Set and get
        cache.set("key", "value")
        assert cache.get("key") == "value"
        
        # Overwrite
        cache.set("key", "new_value")
        assert cache.get("key") == "new_value"
        
        # Clear
        cache.clear()
        assert cache.get("key") is None
    
    def test_memory_cache_ttl_expiration(self):
        """Test MemoryCache TTL expiration."""
        cache = MemoryCache(default_ttl_s=1)
        
        # Set value
        cache.set("key", "value")
        assert cache.get("key") == "value"
        
        # Mock time passage
        current_time = time.time()
        with patch('time.time') as mock_time:
            mock_time.return_value = current_time + 2  # 2 seconds later
            
            # Should be expired
            assert cache.get("key") is None
    
    def test_memory_cache_custom_ttl(self):
        """Test MemoryCache with custom TTL per entry."""
        cache = MemoryCache()
        
        # Set with custom TTL
        current_time = time.time()
        with patch('time.time') as mock_time:
            mock_time.return_value = current_time
            
            cache.set("key", "value", ttl_s=1)
            assert cache.get("key") == "value"
            
            # Mock time passage
            mock_time.return_value = current_time + 2  # 2 seconds later
            
            # Should be expired
            assert cache.get("key") is None
    
    def test_memory_cache_size(self):
        """Test MemoryCache size calculation."""
        cache = MemoryCache()
        
        assert cache.size() == 0
        
        cache.set("key1", "value1")
        assert cache.size() == 1
        
        cache.set("key2", "value2")
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0


class TestAiClientCaching:
    """Test AiClient caching integration."""
    
    def test_ask_caches_when_enabled_and_temp_low(self):
        """Test that ask() caches when enabled and temperature is low."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory", cache_max_temperature=0.7)
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # First call
        response1 = client.ask("hello", temperature=0.2)
        assert provider.ask_count == 1
        
        # Second call should hit cache
        response2 = client.ask("hello", temperature=0.2)
        assert provider.ask_count == 1  # No additional call
        assert response1 == response2
    
    def test_ask_does_not_cache_when_disabled(self):
        """Test that ask() doesn't cache when disabled."""
        settings = AiSettings(cache_enabled=False)
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # First call
        client.ask("hello", temperature=0.2)
        assert provider.ask_count == 1
        
        # Second call should not hit cache
        client.ask("hello", temperature=0.2)
        assert provider.ask_count == 2
    
    def test_ask_does_not_cache_when_temp_high(self):
        """Test that ask() doesn't cache when temperature is too high."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory", cache_max_temperature=0.7)
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Call with high temperature
        client.ask("hello", temperature=0.9)
        assert provider.ask_count == 1
        
        # Second call should not hit cache (temp too high)
        client.ask("hello", temperature=0.9)
        assert provider.ask_count == 2
    
    def test_ask_cache_key_model_sensitive(self):
        """Test that cache keys are sensitive to model."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Call with different models
        client.ask("hello", model="model1")
        assert provider.ask_count == 1
        
        client.ask("hello", model="model2")
        assert provider.ask_count == 2  # Different cache key
        
        # Same model should hit cache
        client.ask("hello", model="model1")
        assert provider.ask_count == 2  # No additional call
    
    def test_ask_cache_key_parameter_sensitive(self):
        """Test that cache keys are sensitive to relevant parameters."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Call with different temperatures
        client.ask("hello", temperature=0.1)
        assert provider.ask_count == 1
        
        client.ask("hello", temperature=0.3)
        assert provider.ask_count == 2  # Different cache key
        
        # Same temperature should hit cache
        client.ask("hello", temperature=0.1)
        assert provider.ask_count == 2  # No additional call
    
    def test_ask_does_not_cache_list_prompts(self):
        """Test that list prompts are not cached in Phase 1."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Call with list prompt
        client.ask(["hello", "world"])
        assert provider.ask_many_count == 1
        
        # Second call should not hit cache
        client.ask(["hello", "world"])
        assert provider.ask_many_count == 2
    
    def test_ask_json_caches_parsed_result(self):
        """Test that ask_json() caches the parsed Python object."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Override ask_text to return predictable JSON and track calls
        call_count = 0
        original_ask_text = provider.ask_text
        def json_ask_text(prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            return '{"result": "value"}'
        provider.ask_text = json_ask_text
        
        # First call
        result1 = client.ask_json("data")
        assert call_count == 1
        assert isinstance(result1, dict)
        assert result1["result"] == "value"
        
        # Second call should hit cache
        result2 = client.ask_json("data")
        assert call_count == 1  # No additional call
        assert result1 == result2
    
    def test_ask_json_does_not_cache_failure(self):
        """Test that ask_json() doesn't cache JSON parsing failures."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Clear any existing cache and use unique prompt
        client.cache.clear()
        
        # Override the ask_text method to return invalid JSON for both original and repair prompts
        def failing_ask_text(prompt, **kwargs):
            if "bad_json_test_12345" in prompt:
                return "invalid json {"
            return '{"result": "value"}'
        provider.ask_text = failing_ask_text
        
        # First call should fail (no repairs allowed)
        with pytest.raises(JsonParseError):
            client.ask_json("bad_json_test_12345", max_repairs=0)
        
        # Second call should also fail and not hit cache
        with pytest.raises(JsonParseError):
            client.ask_json("bad_json_test_12345", max_repairs=0)
    
    def test_ask_json_cache_key_includes_repairs(self):
        """Test that ask_json cache keys include max_repairs parameter."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Override ask_text to return predictable JSON and track calls
        call_count = 0
        def json_ask_text(prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            return '{"result": "value"}'
        provider.ask_text = json_ask_text
        
        # Call with different max_repairs
        client.ask_json("data", max_repairs=1)
        assert call_count == 1
        
        client.ask_json("data", max_repairs=2)
        assert call_count == 2  # Different cache key
        
        # Same max_repairs should hit cache
        client.ask_json("data", max_repairs=1)
        assert call_count == 2  # No additional call
    
    def test_embeddings_caches(self):
        """Test that get_embeddings() works correctly (note: doesn't use cache currently)."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory", api_key="test-key")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        # Mock OpenAI embeddings
        mock_embeddings = Mock()
        mock_embeddings.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6])
        ]
        
        with patch('ai_utilities.client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_embeddings
            mock_openai.return_value = mock_client
            
            # First call
            result1 = client.get_embeddings(["hello", "world"])
            assert mock_client.embeddings.create.call_count == 1
            assert len(result1) == 2
            assert result1[0] == [0.1, 0.2, 0.3]
            
            # Second call (note: embeddings doesn't use cache currently)
            result2 = client.get_embeddings(["hello", "world"])
            assert mock_client.embeddings.create.call_count == 2  # Makes another call
            assert result1 == result2
    
    def test_embeddings_cache_key_sensitive(self):
        """Test that embeddings calls work correctly with different inputs (note: doesn't use cache currently)."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory", api_key="test-key")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider)
        
        mock_embeddings = Mock()
        mock_embeddings.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        
        with patch('ai_utilities.client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_embeddings
            mock_openai.return_value = mock_client
            
            # Different texts should make different calls
            client.get_embeddings(["hello"])
            assert mock_client.embeddings.create.call_count == 1
            
            client.get_embeddings(["world"])
            assert mock_client.embeddings.create.call_count == 2
            
            # Same text should make another call (no caching currently)
            client.get_embeddings(["hello"])
            assert mock_client.embeddings.create.call_count == 3  # Makes another call
    
    def test_explicit_cache_backend_overrides_settings(self):
        """Test that explicit cache backend overrides settings."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        explicit_cache = NullCache()  # Override with null cache
        
        client = AiClient(settings=settings, provider=provider, cache=explicit_cache)
        
        # Should not cache despite settings
        client.ask("hello", temperature=0.2)
        assert provider.ask_count == 1
        
        client.ask("hello", temperature=0.2)
        assert provider.ask_count == 2  # No caching occurred
    
    def test_cache_usage_tracking(self):
        """Test that cached responses are tracked in usage stats."""
        settings = AiSettings(cache_enabled=True, cache_backend="memory")
        provider = FakeProvider(settings)
        client = AiClient(settings=settings, provider=provider, track_usage=True)
        
        # First call
        client.ask("hello", temperature=0.2)
        initial_usage = client.get_usage_stats()
        
        # Second cached call should increment usage
        client.ask("hello", temperature=0.2)
        cached_usage = client.get_usage_stats()
        
        # Usage should be tracked for cached responses too
        assert cached_usage.total_tokens > initial_usage.total_tokens


class TestCacheHelpers:
    """Test cache helper functions."""
    
    def test_stable_hash_deterministic(self):
        """Test that stable_hash is deterministic."""
        data = {"key": "value", "number": 42}
        
        hash1 = stable_hash(data)
        hash2 = stable_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_stable_hash_order_independent(self):
        """Test that stable_hash is independent of key order."""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}
        
        hash1 = stable_hash(data1)
        hash2 = stable_hash(data2)
        
        assert hash1 == hash2
    
    def test_stable_hash_different_data(self):
        """Test that stable_hash produces different hashes for different data."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        
        hash1 = stable_hash(data1)
        hash2 = stable_hash(data2)
        
        assert hash1 != hash2


if __name__ == "__main__":
    pytest.main([__file__])
