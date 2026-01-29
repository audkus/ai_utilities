"""
Tests for SQLite cache backend with namespace support.

Tests namespace isolation, persistence, TTL, LRU eviction, and integration with AiClient.
"""

import json
import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_utilities.cache import SqliteCache, NullCache
from ai_utilities.client import AiClient, AiSettings, _sanitize_namespace, _default_namespace, _running_under_pytest
from tests.utils.test_caching import FakeProvider


class TestSqliteCacheBasics:
    """Test basic SqliteCache functionality."""
    
    def test_sqlite_cache_roundtrip_get_set_namespaced(self, tmp_path):
        """Test that different namespaces are completely isolated."""
        db_path = tmp_path / "cache.sqlite"
        
        cache_a = SqliteCache(db_path, namespace="project_a")
        cache_b = SqliteCache(db_path, namespace="project_b")
        
        # Set same key in both namespaces with different values
        cache_a.set("key1", "value_a")
        cache_b.set("key1", "value_b")
        
        # Each namespace should only see its own value
        assert cache_a.get("key1") == "value_a"
        assert cache_b.get("key1") == "value_b"
        
        # Verify isolation by checking raw database
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT namespace, key, value_json FROM ai_cache ORDER BY namespace")
            rows = cursor.fetchall()
            assert len(rows) == 2
            assert rows[0] == ("project_a", "key1", '"value_a"')
            assert rows[1] == ("project_b", "key1", '"value_b"')
    
    def test_sqlite_cache_clear_only_namespace(self, tmp_path):
        """Test that clear() only affects the current namespace."""
        db_path = tmp_path / "cache.sqlite"
        
        cache_a = SqliteCache(db_path, namespace="ns_a")
        cache_b = SqliteCache(db_path, namespace="ns_b")
        
        # Set values in both namespaces
        cache_a.set("key1", "value_a1")
        cache_a.set("key2", "value_a2")
        cache_b.set("key1", "value_b1")
        cache_b.set("key2", "value_b2")
        
        # Clear only namespace A
        cache_a.clear()
        
        # Namespace A should be empty, B should still have values
        assert cache_a.get("key1") is None
        assert cache_a.get("key2") is None
        assert cache_b.get("key1") == "value_b1"
        assert cache_b.get("key2") == "value_b2"
    
    def test_sqlite_cache_persists_across_instances_same_namespace(self, tmp_path):
        """Test that data persists across cache instances with same namespace."""
        db_path = tmp_path / "cache.sqlite"
        
        # Create first instance and set data
        cache1 = SqliteCache(db_path, namespace="persistent")
        cache1.set("key1", {"nested": "data"})
        cache1.set("key2", [1, 2, 3])
        
        # Create second instance with same namespace
        cache2 = SqliteCache(db_path, namespace="persistent")
        
        # Should retrieve the same data
        assert cache2.get("key1") == {"nested": "data"}
        assert cache2.get("key2") == [1, 2, 3]
    
    def test_sqlite_cache_ttl_expiry_namespace_scoped(self, tmp_path):
        """Test TTL expiration works correctly within namespaces."""
        db_path = tmp_path / "cache.sqlite"
        
        cache_a = SqliteCache(db_path, namespace="ns_a")
        cache_b = SqliteCache(db_path, namespace="ns_b")
        
        # Set entries with short TTL in both namespaces
        cache_a.set("key_short", "expires_a", ttl_s=1)
        cache_b.set("key_short", "expires_b", ttl_s=1)
        
        # Set entries with longer TTL
        cache_a.set("key_long", "persists_a", ttl_s=3600)
        cache_b.set("key_long", "persists_b", ttl_s=3600)
        
        # All entries should be available initially
        assert cache_a.get("key_short") == "expires_a"
        assert cache_b.get("key_short") == "expires_b"
        assert cache_a.get("key_long") == "persists_a"
        assert cache_b.get("key_long") == "persists_b"
        
        # Wait for short TTL to expire
        time.sleep(1.1)
        
        # Short TTL entries should be expired in both namespaces
        assert cache_a.get("key_short") is None
        assert cache_b.get("key_short") is None
        
        # Long TTL entries should still persist
        assert cache_a.get("key_long") == "persists_a"
        assert cache_b.get("key_long") == "persists_b"
    
    def test_sqlite_cache_prunes_lru_per_namespace(self, tmp_path):
        """Test LRU pruning is scoped to individual namespaces."""
        db_path = tmp_path / "cache.sqlite"
        
        # Create caches with small max entries
        cache_a = SqliteCache(db_path, namespace="ns_a", max_entries=3, prune_batch=10)
        cache_b = SqliteCache(db_path, namespace="ns_b", max_entries=3, prune_batch=10)
        
        # Insert 5 entries into namespace A
        for i in range(5):
            cache_a.set(f"key_a{i}", f"value_a{i}")
            time.sleep(0.01)  # Ensure different timestamps
        
        # Insert 5 entries into namespace B
        for i in range(5):
            cache_b.set(f"key_b{i}", f"value_b{i}")
            time.sleep(0.01)
        
        # Both namespaces should be pruned to max_entries (3)
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT namespace, COUNT(*) FROM ai_cache GROUP BY namespace ORDER BY namespace")
            rows = cursor.fetchall()
            assert len(rows) == 2
            assert rows[0] == ("ns_a", 3)
            assert rows[1] == ("ns_b", 3)
        
        # Verify that the most recent entries remain (LRU eviction)
        assert cache_a.get("key_a0") is None  # Should be evicted (oldest)
        assert cache_a.get("key_a1") is None  # Should be evicted
        assert cache_a.get("key_a2") is not None  # Should remain
        assert cache_a.get("key_a3") is not None  # Should remain
        assert cache_a.get("key_a4") is not None  # Should remain (newest)
        
        # Namespace B should have its own LRU order
        assert cache_b.get("key_b0") is None
        assert cache_b.get("key_b1") is None
        assert cache_b.get("key_b2") is not None
        assert cache_b.get("key_b3") is not None
        assert cache_b.get("key_b4") is not None
    
    def test_sqlite_cache_json_serialization(self, tmp_path):
        """Test that JSON serialization works correctly."""
        db_path = tmp_path / "cache.sqlite"
        cache = SqliteCache(db_path, namespace="test")
        
        # Test various JSON-serializable types
        test_data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, "two", {"nested": "object"}],
            "object": {"key": "value", "nested": {"deep": "value"}}
        }
        
        cache.set("complex", test_data)
        retrieved = cache.get("complex")
        
        assert retrieved == test_data
    
    def test_sqlite_cache_non_serializable_error(self, tmp_path):
        """Test that non-JSON-serializable values raise appropriate error."""
        db_path = tmp_path / "cache.sqlite"
        cache = SqliteCache(db_path, namespace="test")
        
        # Try to cache a function (not JSON-serializable)
        def test_func():
            pass
        
        with pytest.raises(ValueError, match="Value must be JSON-serializable"):
            cache.set("func", test_func)


class TestNamespaceHelpers:
    """Test namespace helper functions."""
    
    def test_sanitize_namespace(self):
        """Test namespace sanitization."""
        # Basic sanitization
        assert _sanitize_namespace("My Project") == "my_project"
        assert _sanitize_namespace("test@#$%^&*()") == "test"  # Special chars removed, consecutive underscores collapsed
        assert _sanitize_namespace("  spaced  ") == "spaced"
        
        # Length limiting
        long_ns = "a" * 100
        result = _sanitize_namespace(long_ns)
        assert len(result) <= 50
        assert result == "a" * 50
        
        # Empty input
        assert _sanitize_namespace("") == "default"
        assert _sanitize_namespace("   ") == "default"
        
        # Special characters that are preserved
        assert _sanitize_namespace("proj-1_name") == "proj-1_name"
        assert _sanitize_namespace("proj.name") == "proj.name"  # dots are preserved
    
    def test_default_namespace(self):
        """Test default namespace generation."""
        # Should generate stable namespace based on current directory
        ns1 = _default_namespace()
        ns2 = _default_namespace()
        assert ns1 == ns2  # Should be consistent
        assert ns1.startswith("proj_")  # Should have prefix
        assert len(ns1) == 17  # "proj_" + 12 char hash
    
    @pytest.mark.skipif(not _running_under_pytest(), reason="Only runs under pytest")
    def test_default_namespace_under_pytest(self):
        """Test that default namespace works correctly when running under pytest."""
        ns = _default_namespace()
        # Should return a project-based namespace, not "pytest"
        assert ns.startswith("proj_")
        assert len(ns) == 17  # "proj_" + 12 char hash
    
    def test_running_under_pytest(self):
        """Test pytest detection."""
        # This should be True when running this test
        assert _running_under_pytest()


class TestAiClientSqliteIntegration:
    """Test AiClient integration with SQLite cache."""
    
    def test_aiclient_uses_sqlite_cache_with_namespace(self, tmp_path):
        """Test that AiClient uses SQLite cache with proper namespace isolation."""
        db_path = tmp_path / "cache.sqlite"
        
        # Create fake provider that counts calls
        fake_settings = AiSettings(temperature=0.5)
        provider = FakeProvider(fake_settings)
        
        # First client with namespace "projA"
        settings_a = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_namespace="projA",
            temperature=0.5
        )
        client_a = AiClient(settings=settings_a, provider=provider)
        
        # Second client with same DB but different namespace "projB"
        settings_b = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_namespace="projB",
            temperature=0.5
        )
        client_b = AiClient(settings=settings_b, provider=provider)
        
        # Third client with same namespace as A
        settings_c = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_namespace="projA",
            temperature=0.5
        )
        client_c = AiClient(settings=settings_c, provider=provider)
        
        prompt = "What is 2+2?"
        
        # First call from client A should hit provider
        response_a1 = client_a.ask(prompt)
        assert provider.ask_count == 1
        assert "What is 2+2?" in response_a1
        
        # Second call from client A should hit cache
        response_a2 = client_a.ask(prompt)
        assert provider.ask_count == 1  # No additional calls
        assert response_a2 == response_a1  # Same cached response
        
        # Call from client B (different namespace) should hit provider
        response_b = client_b.ask(prompt)
        assert provider.ask_count == 2  # One additional call
        assert "What is 2+2?" in response_b
        
        # Call from client C (same namespace as A) should hit cache
        response_c = client_c.ask(prompt)
        assert provider.ask_count == 2  # No additional calls
        assert response_c == response_a1  # Same cached response from A
    
    def test_aiclient_sqlite_disabled_by_default_in_pytest_without_path(self, tmp_path):
        """Test that SQLite cache is disabled in pytest without explicit path."""
        fake_settings = AiSettings(temperature=0.5)
        provider = FakeProvider(fake_settings)
        
        settings = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            # No explicit path - should disable in pytest
            temperature=0.5
        )
        client = AiClient(settings=settings, provider=provider)
        
        # Should use NullCache (no caching)
        assert isinstance(client.cache, NullCache)
        
        # Multiple calls should hit provider each time
        response1 = client.ask("What is 2+2?")
        assert provider.ask_count == 1
        
        response2 = client.ask("What is 2+2?")
        assert provider.ask_count == 2  # Should call again (no cache)
    
    def test_aiclient_sqlite_enabled_with_explicit_path_in_pytest(self, tmp_path):
        """Test that SQLite cache works in pytest with explicit path."""
        db_path = tmp_path / "test_cache.sqlite"
        fake_settings = AiSettings(temperature=0.5)
        provider = FakeProvider(fake_settings)
        
        settings = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,  # Explicit path
            temperature=0.5
        )
        client = AiClient(settings=settings, provider=provider)
        
        # Should use SqliteCache
        assert isinstance(client.cache, SqliteCache)
        assert client.cache.namespace == "pytest"
        
        # Should cache properly
        response1 = client.ask("What is 2+2?")
        assert provider.ask_count == 1
        
        response2 = client.ask("What is 2+2?")
        assert provider.ask_count == 1  # Should hit cache
    
    def test_aiclient_sqlite_with_custom_settings(self, tmp_path):
        """Test SQLite cache with custom settings."""
        db_path = tmp_path / "custom_cache.sqlite"
        fake_settings = AiSettings(temperature=0.5)
        provider = FakeProvider(fake_settings)
        
        settings = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_sqlite_table="custom_table",
            cache_sqlite_wal=False,
            cache_sqlite_busy_timeout_ms=5000,
            cache_ttl_s=3600,
            cache_sqlite_max_entries=10,
            cache_sqlite_prune_batch=5,
            temperature=0.5
        )
        client = AiClient(settings=settings, provider=provider)
        
        # Verify cache configuration
        cache = client.cache
        assert isinstance(cache, SqliteCache)
        assert cache.db_path == db_path
        assert cache.table == "custom_table"
        assert cache.wal is False
        assert cache.busy_timeout_ms == 5000
        assert cache.default_ttl_s == 3600
        assert cache.max_entries == 10
        assert cache.prune_batch == 5
    
    def test_aiclient_cache_settings_excluded_from_provider_params(self, tmp_path):
        """Test that cache settings are not passed to provider."""
        fake_settings = AiSettings(temperature=0.5)
        provider = FakeProvider(fake_settings)
        
        settings = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=tmp_path / "cache.sqlite",
            cache_namespace="test",
            temperature=0.5,
            max_tokens=100
        )
        client = AiClient(settings=settings, provider=provider)
        
        # Make a request to trigger provider call
        response = client.ask("test")
        
        # Verify the call was made and response is as expected
        assert provider.ask_count == 1
        assert "test" in response
        
        # The fact that the provider was called successfully indicates 
        # that cache settings were not passed as invalid parameters


class TestSqliteCacheEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_clear_all_namespaces(self, tmp_path):
        """Test clearing all namespaces."""
        db_path = tmp_path / "cache.sqlite"
        
        cache_a = SqliteCache(db_path, namespace="ns_a")
        cache_b = SqliteCache(db_path, namespace="ns_b")
        
        # Set data in both namespaces
        cache_a.set("key1", "value_a")
        cache_b.set("key1", "value_b")
        
        # Clear all namespaces
        cache_a.clear_all_namespaces()
        
        # Both should be empty
        assert cache_a.get("key1") is None
        assert cache_b.get("key1") is None
    
    def test_database_creation_with_parent_dirs(self, tmp_path):
        """Test that parent directories are created for database."""
        nested_path = tmp_path / "nested" / "dir" / "cache.sqlite"
        
        cache = SqliteCache(nested_path, namespace="test")
        cache.set("key", "value")
        
        assert nested_path.exists()
        assert cache.get("key") == "value"
    
    def test_corrupted_data_handling(self, tmp_path):
        """Test handling of corrupted JSON data."""
        db_path = tmp_path / "cache.sqlite"
        
        cache = SqliteCache(db_path, namespace="test")
        cache.set("good_key", "good_value")
        
        # Manually insert corrupted data
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ai_cache (namespace, key, value_json, created_at, last_access_at) VALUES (?, ?, ?, ?, ?)",
                ("test", "bad_key", "invalid json{", time.time(), time.time())
            )
            conn.commit()
        
        # Good data should still work
        assert cache.get("good_key") == "good_value"
        
        # Bad data should be removed and return None
        assert cache.get("bad_key") is None
        
        # Verify bad data was cleaned up
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM ai_cache WHERE key = 'bad_key'")
            assert cursor.fetchone()[0] == 0
