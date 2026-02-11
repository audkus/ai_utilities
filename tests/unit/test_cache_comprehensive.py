"""Comprehensive cache tests for Phase 2 - Caching functionality."""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from ai_utilities import AiSettings, AiClient
from ai_utilities.cache import (
    CacheBackend, NullCache, MemoryCache, SqliteCache,
    stable_hash, normalize_prompt
)
from tests.fake_provider import FakeProvider


class TestCacheBackends:
    """Test cache backend implementations."""
    
    def test_null_cache_behavior(self):
        """Test NullCache never caches anything."""
        cache = NullCache()
        
        # Should never store anything
        cache.set("key", "value")
        assert cache.get("key") is None
        
        # Should handle any key/value types
        cache.set("any_key", {"complex": "object"})
        assert cache.get("any_key") is None
        
        # Clear should be no-op
        cache.clear()
        assert cache.get("key") is None
    
    def test_memory_cache_basic_operations(self):
        """Test MemoryCache basic get/set operations."""
        cache = MemoryCache()
        
        # Test setting and getting
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
        
        # Test overwriting
        cache.set("key1", "new_value")
        assert cache.get("key1") == "new_value"
        
        # Test complex objects
        test_data = {"nested": {"data": [1, 2, 3]}}
        cache.set("complex", test_data)
        assert cache.get("complex") == test_data
    
    def test_memory_cache_ttl_expiration(self):
        """Test MemoryCache TTL expiration."""
        cache = MemoryCache()
        
        # Set with short TTL
        cache.set("ttl_key", "ttl_value", ttl_s=1)
        assert cache.get("ttl_key") == "ttl_value"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("ttl_key") is None
        
        # Test default TTL
        cache_with_default = MemoryCache(default_ttl_s=1)
        cache_with_default.set("default_ttl", "value")
        assert cache_with_default.get("default_ttl") == "value"
        
        time.sleep(1.1)
        assert cache_with_default.get("default_ttl") is None
    
    def test_memory_cache_no_ttl(self):
        """Test MemoryCache without TTL (persistent)."""
        cache = MemoryCache()
        
        # Set without TTL
        cache.set("persistent", "value")
        assert cache.get("persistent") == "value"
        
        # Should persist after time
        time.sleep(0.1)
        assert cache.get("persistent") == "value"
    
    def test_memory_cache_size_and_clear(self):
        """Test MemoryCache size tracking and clearing."""
        cache = MemoryCache()
        
        assert cache.size() == 0
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.size() == 2
        
        # Clear all
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_memory_cache_thread_safety(self):
        """Test MemoryCache thread safety (basic check)."""
        import threading
        
        cache = MemoryCache()
        results = []
        
        def worker(value):
            cache.set("thread_key", value)
            results.append(cache.get("thread_key"))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(f"value_{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have completed without errors
        assert len(results) == 5
        # All results should be valid strings
        assert all(isinstance(r, str) for r in results)
    
    def test_sqlite_cache_basic_operations(self, tmp_workdir):
        """Test SqliteCache basic operations."""
        db_path = tmp_workdir / "test_cache.db"
        cache = SqliteCache(db_path=db_path, namespace="test")
        
        # Test setting and getting
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
        
        # Test overwriting
        cache.set("key1", "new_value")
        assert cache.get("key1") == "new_value"
        
        # Test complex objects (must be JSON serializable)
        test_data = {"nested": {"data": [1, 2, 3]}}
        cache.set("complex", test_data)
        assert cache.get("complex") == test_data
    
    def test_sqlite_cache_ttl_expiration(self, tmp_workdir):
        """Test SqliteCache TTL expiration."""
        db_path = tmp_workdir / "test_ttl.db"
        cache = SqliteCache(db_path=db_path, namespace="test_ttl")
        
        # Set with short TTL
        cache.set("ttl_key", "ttl_value", ttl_s=1)
        assert cache.get("ttl_key") == "ttl_value"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("ttl_key") is None
    
    def test_sqlite_cache_namespace_isolation(self, tmp_workdir):
        """Test SqliteCache namespace isolation."""
        db_path = tmp_workdir / "test_namespace.db"
        
        cache1 = SqliteCache(db_path=db_path, namespace="ns1")
        cache2 = SqliteCache(db_path=db_path, namespace="ns2")
        
        # Same key, different namespaces
        cache1.set("shared_key", "value1")
        cache2.set("shared_key", "value2")
        
        assert cache1.get("shared_key") == "value1"
        assert cache2.get("shared_key") == "value2"
    
    def test_sqlite_cache_persistence(self, tmp_workdir):
        """Test SqliteCache persistence across instances."""
        db_path = tmp_workdir / "test_persist.db"
        
        # Create first instance and set data
        cache1 = SqliteCache(db_path=db_path, namespace="persist")
        cache1.set("persistent_key", "persistent_value")
        
        # Create second instance and verify data persists
        cache2 = SqliteCache(db_path=db_path, namespace="persist")
        assert cache2.get("persistent_key") == "persistent_value"


class TestCacheUtilities:
    """Test cache utility functions."""
    
    def test_stable_hash_consistency(self):
        """Test stable_hash produces consistent results."""
        data = {"key": "value", "number": 42}
        
        hash1 = stable_hash(data)
        hash2 = stable_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in hash1)
    
    def test_stable_hash_order_independence(self):
        """Test stable_hash is independent of key order."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}
        
        hash1 = stable_hash(data1)
        hash2 = stable_hash(data2)
        
        assert hash1 == hash2
    
    def test_stable_hash_different_data(self):
        """Test stable_hash produces different hashes for different data."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        
        hash1 = stable_hash(data1)
        hash2 = stable_hash(data2)
        
        assert hash1 != hash2
    
    def test_stable_hash_complex_types(self):
        """Test stable_hash with complex nested data."""
        data = {
            "string": "test",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
            "boolean": True,
            "null": None
        }
        
        hash_val = stable_hash(data)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64
    
    def test_normalize_prompt(self):
        """Test prompt normalization."""
        # Should strip trailing whitespace
        assert normalize_prompt("hello world   ") == "hello world"
        assert normalize_prompt("test\n\n\n") == "test"
        assert normalize_prompt("spaces\t\t\t") == "spaces"
        
        # Should preserve leading whitespace and internal spacing
        assert normalize_prompt("  leading") == "  leading"
        assert normalize_prompt("internal  spacing") == "internal  spacing"
        assert normalize_prompt("multiple\nlines") == "multiple\nlines"
        
        # Empty string handling
        assert normalize_prompt("") == ""
        assert normalize_prompt("   ") == ""


class TestCacheConfiguration:
    """Test cache configuration in AiSettings."""
    
    def test_cache_configuration_defaults(self, isolated_env):
        """Test default cache configuration."""
        settings = AiSettings(_env_file=None)
        
        assert settings.cache_enabled is False
        assert settings.cache_backend == "null"
        assert settings.cache_ttl_s is None
        assert settings.cache_max_temperature == 0.7
        assert settings.cache_sqlite_path is None
        assert settings.cache_sqlite_table == "ai_cache"
        assert settings.cache_sqlite_wal is True
        assert settings.cache_sqlite_busy_timeout_ms == 3000
        assert settings.cache_sqlite_max_entries is None
        assert settings.cache_sqlite_prune_batch == 200
        assert settings.cache_namespace is None
    
    def test_cache_configuration_override(self, isolated_env):
        """Test cache configuration override."""
        settings = AiSettings(
            cache_enabled=True,
            cache_backend="memory",
            cache_ttl_s=3600,
            cache_max_temperature=0.5,
            _env_file=None
        )
        
        assert settings.cache_enabled is True
        assert settings.cache_backend == "memory"
        assert settings.cache_ttl_s == 3600
        assert settings.cache_max_temperature == 0.5
    
    def test_cache_configuration_sqlite(self, isolated_env):
        """Test SQLite cache configuration."""
        db_path = Path("/tmp/test_cache.db")
        settings = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_sqlite_table="custom_table",
            cache_sqlite_wal=False,
            cache_sqlite_busy_timeout_ms=5000,
            cache_sqlite_max_entries=1000,
            cache_sqlite_prune_batch=100,
            cache_namespace="test_namespace",
            _env_file=None
        )
        
        assert settings.cache_backend == "sqlite"
        assert settings.cache_sqlite_path == db_path
        assert settings.cache_sqlite_table == "custom_table"
        assert settings.cache_sqlite_wal is False
        assert settings.cache_sqlite_busy_timeout_ms == 5000
        assert settings.cache_sqlite_max_entries == 1000
        assert settings.cache_sqlite_prune_batch == 100
        assert settings.cache_namespace == "test_namespace"


class TestCacheIntegration:
    """Test cache integration with AiClient."""
    
    def test_client_cache_disabled_by_default(self, fake_settings):
        """Test that cache is disabled by default."""
        fake_settings.cache_enabled = False
        fake_provider = FakeProvider()
        client = AiClient(settings=fake_settings, provider=fake_provider)
        
        assert isinstance(client.cache, NullCache)
    
    def test_client_memory_cache_enabled(self, fake_settings):
        """Test memory cache integration."""
        fake_settings.cache_enabled = True
        fake_settings.cache_backend = "memory"
        fake_settings.cache_ttl_s = 3600
        
        fake_provider = FakeProvider()
        client = AiClient(settings=fake_settings, provider=fake_provider)
        
        assert isinstance(client.cache, MemoryCache)
        assert client.cache._default_ttl_s == 3600
    
    def test_client_sqlite_cache_isolated_in_pytest(self, fake_settings):
        """Test SQLite cache is disabled in pytest unless explicit path."""
        fake_settings.cache_enabled = True
        fake_settings.cache_backend = "sqlite"
        # No explicit path set
        
        fake_provider = FakeProvider()
        with patch('ai_utilities.client._running_under_pytest', return_value=True):
            client = AiClient(settings=fake_settings, provider=fake_provider)
            # Should be NullCache due to pytest isolation
            assert isinstance(client.cache, NullCache)
    
    def test_client_sqlite_cache_with_explicit_path(self, fake_settings, tmp_workdir):
        """Test SQLite cache with explicit path."""
        fake_settings.cache_enabled = True
        fake_settings.cache_backend = "sqlite"
        fake_settings.cache_sqlite_path = tmp_workdir / "test.db"
        
        fake_provider = FakeProvider()
        with patch('ai_utilities.client._running_under_pytest', return_value=True):
            client = AiClient(settings=fake_settings, provider=fake_provider)
            assert isinstance(client.cache, SqliteCache)
            assert client.cache.db_path == tmp_workdir / "test.db"
    
    def test_explicit_cache_override(self, fake_settings):
        """Test explicit cache backend override."""
        explicit_cache = MemoryCache(default_ttl_s=1800)
        
        # Even with settings that would create different cache
        fake_settings.cache_enabled = True
        fake_settings.cache_backend = "sqlite"
        
        # Patch provider creation to avoid OpenAI SDK dependency
        with patch("ai_utilities.providers.provider_factory.create_provider") as mock_create_provider:
            mock_create_provider.return_value = Mock(name="provider_stub")
            
            client = AiClient(settings=fake_settings, cache=explicit_cache)
            
            assert client.cache is explicit_cache
            assert client.cache._default_ttl_s == 1800
