"""
Smart caching system for AI utilities.

Provides cache backends and utilities for deterministic, safe caching
of AI responses with configurable TTL and opt-in behavior.
"""

import hashlib
import json
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pydantic.v1 as pydantic


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        """Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_s: Time to live in seconds (None for no expiration)
        """
        pass
    
    def clear(self) -> None:
        """Clear all cached values. Optional but useful for tests."""
        pass


class NullCache(CacheBackend):
    """Cache backend that never caches anything."""
    
    def get(self, key: str) -> Optional[Any]:
        """Always returns None - no caching."""
        return None
    
    def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        """No-op - doesn't cache anything."""
        pass
    
    def clear(self) -> None:
        """No-op - nothing to clear."""
        pass


class MemoryCache(CacheBackend):
    """Thread-safe in-memory cache with optional TTL support."""
    
    def __init__(self, default_ttl_s: Optional[int] = None):
        """Initialize memory cache.
        
        Args:
            default_ttl_s: Default TTL in seconds for entries without explicit TTL
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._default_ttl_s = default_ttl_s
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, respecting TTL."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            expires_at = entry.get("expires_at")
            
            # Check if expired
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None
            
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            # Use provided TTL or default
            actual_ttl = ttl_s if ttl_s is not None else self._default_ttl_s
            
            expires_at = None
            if actual_ttl is not None:
                expires_at = time.time() + actual_ttl
            
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
            }
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached entries."""
        with self._lock:
            # Clean expired entries first
            self._clean_expired()
            return len(self._cache)
    
    def _clean_expired(self) -> None:
        """Remove expired entries. Must be called with lock held."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.get("expires_at") is not None and current_time > entry["expires_at"]
        ]
        for key in expired_keys:
            del self._cache[key]


def stable_hash(data: Any) -> str:
    """Create stable hash from data using JSON serialization.
    
    Args:
        data: Any JSON-serializable data
        
    Returns:
        SHA256 hash as hex string
    """
    # Use deterministic JSON serialization
    json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()


def normalize_prompt(prompt: str) -> str:
    """Normalize prompt for caching.
    
    Strips trailing whitespace while preserving semantic meaning.
    
    Args:
        prompt: Input prompt string
        
    Returns:
        Normalized prompt string
    """
    return prompt.rstrip()


# Type alias for cache backends
CacheBackendType = Union[NullCache, MemoryCache]
