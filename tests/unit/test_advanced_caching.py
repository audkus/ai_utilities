"""Additional tests for caching functionality and edge cases."""

import tempfile
from pathlib import Path

from ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider


class TestAdvancedCaching:
    """Test advanced caching scenarios and edge cases."""

    def test_cache_with_different_temperature_settings(self):
        """Test that caching respects temperature settings."""
        fake_provider = FakeProvider(["response for {prompt}"])

        # Enable caching with low temperature threshold
        settings = AiSettings(
            api_key="test-key",
            cache_enabled=True,
            cache_backend="memory",
            cache_max_temperature=0.5,
        )

        client = AiClient(settings, provider=fake_provider)

        # High temperature request should not be cached
        response1 = client.ask("test", temperature=0.8)
        client.ask("test", temperature=0.8)

        # Should call provider twice (not cached due to high temp)
        assert fake_provider.call_count == 2

        # Reset provider
        fake_provider.call_count = 0

        # Low temperature request should be cached
        response3 = client.ask("test", temperature=0.3)
        client.ask("test", temperature=0.3)

        # Should call provider once (cached due to low temp)
        assert fake_provider.call_count == 1

        # All responses should be valid
        assert "response for test" in response1
        assert "response for test" in response3

    def test_cache_namespace_isolation(self):
        """Test that different cache namespaces are properly isolated."""
        fake_provider = FakeProvider(["response for {prompt}"])

        # Create two clients with different cache namespaces
        settings1 = AiSettings(
            api_key="test-key",
            cache_enabled=True,
            cache_backend="memory",
            cache_namespace="client_a",
        )

        settings2 = AiSettings(
            api_key="test-key",
            cache_enabled=True,
            cache_backend="memory",
            cache_namespace="client_b",
        )

        client1 = AiClient(settings1, provider=fake_provider)
        client2 = AiClient(settings2, provider=fake_provider)

        # Both clients should make their own calls (separate caches)
        client1.ask("test")
        client2.ask("test")

        assert fake_provider.call_count == 2

        # Second calls should use各自的 caches
        client1.ask("test")
        client2.ask("test")

        # No additional calls should be made (using cache)
        assert fake_provider.call_count == 2

    def test_cache_basic_functionality_with_ttl(self):
        """Test that cache works with TTL settings."""
        fake_provider = FakeProvider(["response for test"])

        # Create settings with cache TTL
        settings = AiSettings(
            api_key="test-key",
            cache_enabled=True,
            cache_backend="memory",
            cache_ttl_s=3600,  # Long TTL
        )

        client = AiClient(settings, provider=fake_provider)

        # First call
        response1 = client.ask("test")
        assert fake_provider.call_count == 1

        # Immediate second call should use cache
        response2 = client.ask("test")
        assert fake_provider.call_count == 1  # Should use cache

        # Verify responses
        assert response1 == "response for test"
        assert response2 == "response for test"

    def test_cache_with_parameter_variations(self):
        """Test that requests with different parameters are cached separately."""
        fake_provider = FakeProvider(["response for test"])

        settings = AiSettings(
            api_key="test-key", cache_enabled=True, cache_backend="memory"
        )

        client = AiClient(settings, provider=fake_provider)

        # Different parameters should create separate cache entries
        response1 = client.ask("test", temperature=0.5)
        response2 = client.ask("test", temperature=0.7)
        response3 = client.ask("test", temperature=0.5)  # Same as first

        assert fake_provider.call_count == 2  # Two unique parameter sets

        # Verify responses are the same (FakeProvider doesn't vary by params)
        assert response1 == "response for test"
        assert response2 == "response for test"
        assert response3 == "response for test"

    def test_cache_basic_functionality(self):
        """Test that basic cache functionality works."""
        fake_provider = FakeProvider(["response for test"])

        settings = AiSettings(
            api_key="test-key", cache_enabled=True, cache_backend="memory"
        )

        client = AiClient(settings, provider=fake_provider)

        # Should work with cache enabled
        response = client.ask("test")
        assert "response for test" in response
        assert fake_provider.call_count == 1

        # Second call should use cache
        client.ask("test")
        assert fake_provider.call_count == 1  # No additional call

    def test_cache_disabled_fallback(self):
        """Test that disabling cache works correctly."""
        fake_provider = FakeProvider(["response for test"])

        settings = AiSettings(
            api_key="test-key",
            cache_enabled=False,  # Explicitly disabled
        )

        client = AiClient(settings, provider=fake_provider)

        # All calls should go to provider (no caching)
        response1 = client.ask("test")
        response2 = client.ask("test")
        response3 = client.ask("test")

        assert fake_provider.call_count == 3
        assert "response for test" in response1
        assert "response for test" in response2
        assert "response for test" in response3

    def test_sqlite_cache_persistence(self):
        """Test that SQLite cache persists across client instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_cache.sqlite"

            fake_provider = FakeProvider(["persistent response"])

            # Create first client with SQLite cache
            settings1 = AiSettings(
                api_key="test-key",
                cache_enabled=True,
                cache_backend="sqlite",
                cache_sqlite_path=db_path,
                cache_namespace="test",
            )

            client1 = AiClient(settings1, provider=fake_provider)

            # Make a request to populate cache
            response1 = client1.ask("test")
            assert fake_provider.call_count == 1

            # Create second client with same cache
            settings2 = AiSettings(
                api_key="test-key",
                cache_enabled=True,
                cache_backend="sqlite",
                cache_sqlite_path=db_path,
                cache_namespace="test",
            )

            client2 = AiClient(settings2, provider=fake_provider)

            # Should use cached response
            response2 = client2.ask("test")
            assert fake_provider.call_count == 1  # No additional call

            assert response1 == response2

    def test_cache_key_generation_stability(self):
        """Test that cache keys are generated consistently."""
        fake_provider = FakeProvider(["response for {prompt}"])

        settings = AiSettings(
            api_key="test-key", cache_enabled=True, cache_backend="memory"
        )

        client = AiClient(settings, provider=fake_provider)

        # Multiple identical requests should generate same cache key
        for i in range(5):
            client.ask("test", temperature=0.7, max_tokens=100)

        # Should only call provider once (all others cached)
        assert fake_provider.call_count == 1

    def test_cache_with_null_backend(self):
        """Test that NullCache backend works (no caching)."""
        fake_provider = FakeProvider(["response for {prompt}"])

        settings = AiSettings(
            api_key="test-key",
            cache_enabled=True,
            cache_backend="null",  # Explicit null backend
        )

        client = AiClient(settings, provider=fake_provider)

        # Should never cache with null backend
        for i in range(3):
            client.ask("test")

        assert fake_provider.call_count == 3
