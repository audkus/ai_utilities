"""
Smart caching system for AI utilities.

Provides cache backends and utilities for deterministic, safe caching
of AI responses with configurable TTL and opt-in behavior.
"""

import hashlib
import json
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union



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


class SqliteCache(CacheBackend):
    """SQLite-based persistent cache backend with namespace support.
    
    Provides thread-safe, persistent caching with TTL, LRU eviction, and namespace isolation.
    """
    
    def __init__(
        self,
        db_path: Path,
        table: str = "ai_cache",
        namespace: str = "default",
        wal: bool = True,
        busy_timeout_ms: int = 3000,
        default_ttl_s: Optional[int] = None,
        max_entries: Optional[int] = None,
        prune_batch: int = 200,
    ):
        """Initialize SQLite cache.
        
        Args:
            db_path: Path to SQLite database file
            table: Table name for cache storage
            namespace: Namespace for cache isolation
            wal: Enable WAL mode for better concurrency
            busy_timeout_ms: SQLite busy timeout in milliseconds
            default_ttl_s: Default TTL for entries (None for no expiration)
            max_entries: Maximum entries per namespace (LRU eviction)
            prune_batch: Batch size for LRU pruning operations
        """
        self.db_path = db_path
        self.table = table
        self.namespace = namespace
        self.wal = wal
        self.busy_timeout_ms = busy_timeout_ms
        self.default_ttl_s = default_ttl_s
        self.max_entries = max_entries
        self.prune_batch = prune_batch
        
        # Create database and tables
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema and indexes."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.busy_timeout_ms / 1000.0
        ) as conn:
            # Set pragmas
            if self.wal:
                conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
            
            # Create table with namespace-aware primary key
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_access_at REAL NOT NULL,
                    PRIMARY KEY(namespace, key)
                )
            """)
            
            # Create indexes for performance
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table}_expires 
                ON {self.table} (namespace, expires_at)
            """)
            
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table}_access 
                ON {self.table} (namespace, last_access_at)
            """)
            
            conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.busy_timeout_ms / 1000.0
        ) as conn:
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
            
            cursor = conn.execute(f"""
                SELECT value_json, expires_at FROM {self.table}
                WHERE namespace = ? AND key = ?
            """, (self.namespace, key))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            value_json, expires_at = row
            
            # Check expiration
            if expires_at is not None and time.time() > expires_at:
                # Delete expired entry
                conn.execute(f"""
                    DELETE FROM {self.table}
                    WHERE namespace = ? AND key = ?
                """, (self.namespace, key))
                conn.commit()
                return None
            
            # Update access statistics
            conn.execute(f"""
                UPDATE {self.table}
                SET access_count = access_count + 1, last_access_at = ?
                WHERE namespace = ? AND key = ?
            """, (time.time(), self.namespace, key))
            conn.commit()
            
            # Deserialize and return value
            try:
                return json.loads(value_json)
            except (json.JSONDecodeError, ValueError):
                # Remove corrupted entry
                conn.execute(f"""
                    DELETE FROM {self.table}
                    WHERE namespace = ? AND key = ?
                """, (self.namespace, key))
                conn.commit()
                return None
    
    def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl_s: TTL in seconds (overrides default)
        """
        # Serialize value
        try:
            value_json = json.dumps(value, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON-serializable: {e}")
        
        # Calculate expiration
        ttl = ttl_s if ttl_s is not None else self.default_ttl_s
        expires_at = (time.time() + ttl) if ttl is not None else None
        
        current_time = time.time()
        
        with sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.busy_timeout_ms / 1000.0
        ) as conn:
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
            
            # Insert or replace entry
            conn.execute(f"""
                INSERT OR REPLACE INTO {self.table}
                (namespace, key, value_json, created_at, expires_at, access_count, last_access_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                self.namespace, key, value_json, current_time, expires_at, current_time
            ))
            
            # Prune if necessary
            if self.max_entries is not None:
                self._prune_namespace(conn)
            
            conn.commit()
    
    def clear(self) -> None:
        """Clear all entries in current namespace."""
        with sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.busy_timeout_ms / 1000.0
        ) as conn:
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
            conn.execute(f"""
                DELETE FROM {self.table}
                WHERE namespace = ?
            """, (self.namespace,))
            conn.commit()
    
    def _prune_namespace(self, conn: sqlite3.Connection) -> None:
        """Prune entries in current namespace to stay within max_entries.
        
        Args:
            conn: Active database connection
        """
        # Count entries in namespace
        cursor = conn.execute(f"""
            SELECT COUNT(*) FROM {self.table} WHERE namespace = ?
        """, (self.namespace,))
        
        count = cursor.fetchone()[0]
        if count <= self.max_entries:
            return
        
        # Delete least recently used entries
        entries_to_delete = count - self.max_entries
        conn.execute(f"""
            DELETE FROM {self.table}
            WHERE (namespace, key) IN (
                SELECT namespace, key FROM {self.table}
                WHERE namespace = ?
                ORDER BY last_access_at ASC
                LIMIT ?
            )
        """, (self.namespace, min(entries_to_delete, self.prune_batch)))
    
    def clear_all_namespaces(self) -> None:
        """Clear all entries in all namespaces (for internal/dev use)."""
        with sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.busy_timeout_ms / 1000.0
        ) as conn:
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
            conn.execute(f"DELETE FROM {self.table}")
            conn.commit()


# Type alias for cache backends
CacheBackendType = Union[NullCache, MemoryCache, SqliteCache]
