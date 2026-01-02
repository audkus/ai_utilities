"""Thread-safe usage tracking for AI requests with configurable scoping."""

import json
import os
import threading
import time
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union

import portalocker  # Cross-platform file locking
from pydantic import BaseModel


class UsageScope(Enum):
    """Usage tracking scope options."""
    PER_CLIENT = "per_client"  # Unique tracking per client instance
    PER_PROCESS = "per_process"  # Shared tracking within process
    GLOBAL = "global"  # Global tracking across all processes


class UsageStats(BaseModel):
    """Thread-safe usage statistics for AI requests."""
    tokens_used_today: int = 0
    requests_today: int = 0
    last_reset: str = date.today().isoformat()
    total_tokens: int = 0
    total_requests: int = 0
    client_id: Optional[str] = None  # For per-client tracking
    process_id: Optional[int] = None  # For process tracking


class ThreadSafeUsageTracker:
    """Thread-safe usage tracker with configurable scoping and concurrent access support."""
    
    _shared_locks: Dict[str, threading.RLock] = {}
    
    def __init__(self, 
                 stats_file: Optional[Path] = None,
                 scope: UsageScope = UsageScope.PER_CLIENT,
                 client_id: Optional[str] = None):
        """Initialize thread-safe usage tracker.
        
        Args:
            stats_file: Path to statistics file. If None, generates based on scope.
            scope: Tracking scope (per_client, per_process, global)
            client_id: Unique client identifier for per-client tracking
        """
        self.scope = scope
        self.client_id = client_id or self._generate_client_id()
        self.process_id = os.getpid()
        
        # Generate appropriate file path based on scope
        if stats_file is None:
            stats_file = self._generate_stats_file_path()
        
        self.stats_file = stats_file
        # Use a shared lock based on the file path for proper synchronization
        self._file_lock = self._get_shared_file_lock(stats_file)
        self._memory_cache: Optional[UsageStats] = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 0.0  # Disable cache to ensure data sharing between instances
        
        # Ensure directory exists
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize stats file if it doesn't exist
        self._ensure_stats_file_exists()
    
    def _generate_client_id(self) -> str:
        """Generate a unique client identifier."""
        import uuid
        return f"client_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    @staticmethod
    def _get_shared_file_lock(stats_file: Path) -> threading.RLock:
        """Get a shared lock for a given stats file path.
        
        This ensures that multiple ThreadSafeUsageTracker instances
        using the same stats file share the same lock.
        """
        # Use a class-level dictionary to store locks per file path
        if not hasattr(ThreadSafeUsageTracker, '_shared_locks'):
            ThreadSafeUsageTracker._shared_locks = {}
        
        file_key = str(stats_file.absolute())
        if file_key not in ThreadSafeUsageTracker._shared_locks:
            ThreadSafeUsageTracker._shared_locks[file_key] = threading.RLock()
        
        return ThreadSafeUsageTracker._shared_locks[file_key]
    
    def _generate_stats_file_path(self) -> Path:
        """Generate appropriate stats file path based on scope."""
        base_dir = Path.cwd() / ".ai_utilities" / "usage_stats"
        
        if self.scope == UsageScope.PER_CLIENT:
            return base_dir / f"usage_{self.client_id}.json"
        elif self.scope == UsageScope.PER_PROCESS:
            return base_dir / f"usage_process_{self.process_id}.json"
        else:  # GLOBAL
            return base_dir / "usage_global.json"
    
    def _ensure_stats_file_exists(self):
        """Ensure stats file exists with proper structure."""
        with self._file_lock:
            if not self.stats_file.exists():
                initial_stats = UsageStats(
                    client_id=self.client_id if self.scope == UsageScope.PER_CLIENT else None,
                    process_id=self.process_id if self.scope == UsageScope.PER_PROCESS else None
                )
                self._write_stats_atomic(initial_stats)
    
    def _load_stats(self) -> UsageStats:
        """Load statistics with caching and thread safety."""
        current_time = time.time()
        
        # Check cache first
        if (self._memory_cache and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._memory_cache
        
        with self._file_lock:
            try:
                # Use portalocker for cross-platform file locking
                with open(self.stats_file) as f:
                    portalocker.lock(f, portalocker.LOCK_SH)  # Shared lock for reading
                    data = json.load(f)
                    stats = UsageStats(**data)
                    portalocker.unlock(f)
                
                # Update cache
                self._memory_cache = stats
                self._cache_timestamp = current_time
                return stats
                
            except (json.JSONDecodeError, ValueError, FileNotFoundError):
                # Fallback to fresh stats
                stats = UsageStats(
                    client_id=self.client_id if self.scope == UsageScope.PER_CLIENT else None,
                    process_id=self.process_id if self.scope == UsageScope.PER_PROCESS else None
                )
                self._memory_cache = stats
                self._cache_timestamp = current_time
                return stats
    
    def _write_stats_atomic(self, stats: UsageStats):
        """Write statistics atomically with file locking."""
        # Write to temporary file first, then move atomically
        temp_file = self.stats_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w') as f:
                portalocker.lock(f, portalocker.LOCK_EX)  # Exclusive lock for writing
                json.dump(stats.model_dump(), f, indent=2)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force write to disk
                portalocker.unlock(f)
            
            # Atomic move
            temp_file.replace(self.stats_file)
            
            # Update cache
            self._memory_cache = stats
            self._cache_timestamp = time.time()
            
        except Exception as e:
            # Clean up temp file if something went wrong
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _reset_if_new_day(self, stats: UsageStats) -> UsageStats:
        """Reset daily stats if it's a new day."""
        today = date.today().isoformat()
        if stats.last_reset != today:
            stats.tokens_used_today = 0
            stats.requests_today = 0
            stats.last_reset = today
        return stats
    
    def record_usage(self, tokens_used: int = 0):
        """Record usage from an AI request in a thread-safe manner.
        
        Args:
            tokens_used: Number of tokens used in the request
        """
        with self._file_lock:
            # Load current stats
            stats = self._load_stats()
            
            # Reset if new day
            stats = self._reset_if_new_day(stats)
            
            # Update stats
            stats.tokens_used_today += tokens_used
            stats.requests_today += 1
            stats.total_tokens += tokens_used
            stats.total_requests += 1
            
            # Write back atomically
            self._write_stats_atomic(stats)
    
    def get_stats(self) -> UsageStats:
        """Get current usage statistics in a thread-safe manner."""
        stats = self._load_stats()
        return self._reset_if_new_day(stats)
    
    def print_summary(self):
        """Print a usage summary."""
        stats = self.get_stats()
        print(f"AI Usage Summary (Scope: {self.scope.value}):")
        print(f"  Client ID: {stats.client_id or 'N/A'}")
        print(f"  Process ID: {stats.process_id or 'N/A'}")
        print(f"  Today: {stats.tokens_used_today} tokens, {stats.requests_today} requests")
        print(f"  Total: {stats.total_tokens} tokens, {stats.total_requests} requests")
        print(f"  Stats File: {self.stats_file}")
    
    def get_aggregated_stats(self, scope_filter: Optional[UsageScope] = None) -> Dict[str, UsageStats]:
        """Get aggregated statistics from multiple stats files.
        
        Args:
            scope_filter: Filter by specific scope, None for all
            
        Returns:
            Dictionary mapping file paths to UsageStats
        """
        stats_dir = self.stats_file.parent
        aggregated: Dict[str, UsageStats] = {}
        
        if not stats_dir.exists():
            return aggregated
        
        for stats_file in stats_dir.glob("usage_*.json"):
            try:
                with open(stats_file) as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    data = json.load(f)
                    stats = UsageStats(**data)
                    portalocker.unlock(f)
                    aggregated[str(stats_file)] = stats
            except Exception:
                continue  # Skip corrupted files
        
        return aggregated
    
    def reset_stats(self):
        """Reset all statistics to zero in a thread-safe manner."""
        with self._file_lock:
            reset_stats = UsageStats(
                client_id=self.client_id if self.scope == UsageScope.PER_CLIENT else None,
                process_id=self.process_id if self.scope == UsageScope.PER_PROCESS else None
            )
            self._write_stats_atomic(reset_stats)


# Backward compatibility
UsageTracker = ThreadSafeUsageTracker


# Factory function for easy usage
def create_usage_tracker(scope: Union[str, UsageScope] = UsageScope.PER_CLIENT,
                        stats_file: Optional[Path] = None,
                        client_id: Optional[str] = None) -> ThreadSafeUsageTracker:
    """Create a usage tracker with specified scope.
    
    Args:
        scope: Tracking scope ('per_client', 'per_process', 'global')
        stats_file: Custom stats file path
        client_id: Custom client ID for per-client tracking
        
    Returns:
        ThreadSafeUsageTracker instance
    """
    if isinstance(scope, str):
        scope = UsageScope(scope)
    
    return ThreadSafeUsageTracker(
        stats_file=stats_file,
        scope=scope,
        client_id=client_id
    )
