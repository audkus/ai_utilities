"""Comprehensive tests for usage_tracker.py module - Phase 7B.

This module provides thorough testing for the usage tracking system,
covering thread safety, file operations, scoping, and edge cases.
"""

import json
import os
import tempfile
import threading
import time
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ai_utilities.usage_tracker import (
    UsageScope,
    UsageStats,
    ThreadSafeUsageTracker,
    create_usage_tracker,
    UsageTracker  # Backward compatibility alias
)


class TestUsageScope:
    """Test the UsageScope enum."""
    
    def test_usage_scope_values(self):
        """Test that all expected scope values exist."""
        assert UsageScope.PER_CLIENT.value == "per_client"
        assert UsageScope.PER_PROCESS.value == "per_process"
        assert UsageScope.GLOBAL.value == "global"
    
    def test_usage_scope_creation(self):
        """Test creating UsageScope from string."""
        scope = UsageScope("per_client")
        assert scope == UsageScope.PER_CLIENT
        
        scope = UsageScope("global")
        assert scope == UsageScope.GLOBAL


class TestUsageStats:
    """Test the UsageStats model."""
    
    def test_usage_stats_defaults(self):
        """Test UsageStats with default values."""
        stats = UsageStats()
        
        assert stats.tokens_used_today == 0
        assert stats.requests_today == 0
        assert stats.last_reset == date.today().isoformat()
        assert stats.total_tokens == 0
        assert stats.total_requests == 0
        assert stats.client_id is None
        assert stats.process_id is None
    
    def test_usage_stats_with_values(self):
        """Test UsageStats with custom values."""
        stats = UsageStats(
            tokens_used_today=100,
            requests_today=5,
            last_reset="2023-01-01",
            total_tokens=1000,
            total_requests=50,
            client_id="test_client",
            process_id=12345
        )
        
        assert stats.tokens_used_today == 100
        assert stats.requests_today == 5
        assert stats.last_reset == "2023-01-01"
        assert stats.total_tokens == 1000
        assert stats.total_requests == 50
        assert stats.client_id == "test_client"
        assert stats.process_id == 12345
    
    def test_usage_stats_serialization(self):
        """Test UsageStats serialization and deserialization."""
        original = UsageStats(
            tokens_used_today=50,
            requests_today=3,
            client_id="test"
        )
        
        # Serialize to dict
        data = original.model_dump()
        assert isinstance(data, dict)
        assert data["tokens_used_today"] == 50
        assert data["client_id"] == "test"
        
        # Deserialize from dict
        restored = UsageStats(**data)
        assert restored.tokens_used_today == original.tokens_used_today
        assert restored.client_id == original.client_id


class TestThreadSafeUsageTracker:
    """Test the ThreadSafeUsageTracker class."""
    
    def test_tracker_initialization_per_client(self):
        """Test tracker initialization with per-client scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stats_file = temp_path / "test_stats.json"
            
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.PER_CLIENT,
                client_id="test_client"
            )
            
            assert tracker.scope == UsageScope.PER_CLIENT
            assert tracker.client_id == "test_client"
            assert tracker.process_id == os.getpid()
            assert tracker.stats_file == stats_file
            assert stats_file.exists()
    
    def test_tracker_initialization_auto_generate_client_id(self):
        """Test tracker initialization with auto-generated client ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stats_file = temp_path / "test_stats.json"
            
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.PER_CLIENT
            )
            
            assert tracker.client_id is not None
            assert tracker.client_id.startswith("client_")
            assert len(tracker.client_id) > 10  # Should have UUID and timestamp
    
    def test_tracker_initialization_per_process(self):
        """Test tracker initialization with per-process scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stats_file = temp_path / "test_stats.json"
            
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.PER_PROCESS
            )
            
            assert tracker.scope == UsageScope.PER_PROCESS
            assert tracker.process_id == os.getpid()
    
    def test_tracker_initialization_global(self):
        """Test tracker initialization with global scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stats_file = temp_path / "test_stats.json"
            
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.GLOBAL
            )
            
            assert tracker.scope == UsageScope.GLOBAL
    
    def test_generate_stats_file_path(self):
        """Test stats file path generation for different scopes."""
        # Use a temporary directory instead of mocking Path.cwd
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch('ai_utilities.usage_tracker.Path.cwd') as mock_cwd:
                mock_cwd.return_value = temp_path
                
                # Per-client scope
                tracker = ThreadSafeUsageTracker(
                    scope=UsageScope.PER_CLIENT,
                    client_id="test_client"
                )
                expected = temp_path / ".ai_utilities" / "usage_stats" / "usage_test_client.json"
                assert tracker.stats_file == expected
                
                # Per-process scope
                tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
                expected = temp_path / ".ai_utilities" / "usage_stats" / f"usage_process_{os.getpid()}.json"
                assert tracker.stats_file == expected
                
                # Global scope
                tracker = ThreadSafeUsageTracker(scope=UsageScope.GLOBAL)
                expected = temp_path / ".ai_utilities" / "usage_stats" / "usage_global.json"
                assert tracker.stats_file == expected
    
    def test_generate_client_id(self):
        """Test client ID generation."""
        tracker = ThreadSafeUsageTracker()
        client_id = tracker._generate_client_id()
        
        assert client_id.startswith("client_")
        assert "_" in client_id
        assert len(client_id) > 10
        
        # Should generate different IDs
        client_id2 = tracker._generate_client_id()
        assert client_id != client_id2
    
    def test_get_shared_file_lock(self):
        """Test shared file lock functionality."""
        file_path = Path("/test/shared.json")
        
        lock1 = ThreadSafeUsageTracker._get_shared_file_lock(file_path)
        lock2 = ThreadSafeUsageTracker._get_shared_file_lock(file_path)
        
        # Should return the same lock instance
        assert lock1 is lock2
        assert hasattr(lock1, 'acquire')  # Check it's a lock-like object
    
    def test_record_usage(self):
        """Test recording usage statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            # Record initial usage
            tracker.record_usage(tokens_used=100)
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 100
            assert stats.requests_today == 1
            assert stats.total_tokens == 100
            assert stats.total_requests == 1
            
            # Record more usage
            tracker.record_usage(tokens_used=50)
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 150
            assert stats.requests_today == 2
            assert stats.total_tokens == 150
            assert stats.total_requests == 2
    
    def test_record_usage_zero_tokens(self):
        """Test recording usage with zero tokens."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            tracker.record_usage(tokens_used=0)
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 0
            assert stats.requests_today == 1
            assert stats.total_tokens == 0
            assert stats.total_requests == 1
    
    def test_get_stats(self):
        """Test getting current statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                client_id="test_client"
            )
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 0
            assert stats.requests_today == 0
            assert stats.total_tokens == 0
            assert stats.total_requests == 0
            assert stats.client_id == "test_client"
            assert stats.process_id is None  # PER_CLIENT scope doesn't set process_id
            assert stats.last_reset == date.today().isoformat()
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            # Record some usage
            tracker.record_usage(tokens_used=100)
            tracker.record_usage(tokens_used=50)
            
            # Reset stats
            tracker.reset_stats()
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 0
            assert stats.requests_today == 0
            assert stats.total_tokens == 0
            assert stats.total_requests == 0
            assert stats.last_reset == date.today().isoformat()
    
    def test_print_summary(self, capsys):
        """Test printing usage summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.PER_CLIENT,
                client_id="test_client"
            )
            
            tracker.record_usage(tokens_used=100)
            tracker.print_summary()
            
            captured = capsys.readouterr()
            assert "AI Usage Summary" in captured.out
            assert "per_client" in captured.out
            assert "test_client" in captured.out
            assert "100 tokens" in captured.out
            assert "1 requests" in captured.out
    
    def test_get_aggregated_stats(self):
        """Test getting aggregated statistics from multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple stats files
            stats_dir = Path(temp_dir)
            
            # Create first tracker
            stats_file1 = stats_dir / "usage_client1.json"
            tracker1 = ThreadSafeUsageTracker(
                stats_file=stats_file1,
                client_id="client1"
            )
            tracker1.record_usage(tokens_used=100)
            
            # Create second tracker
            stats_file2 = stats_dir / "usage_client2.json"
            tracker2 = ThreadSafeUsageTracker(
                stats_file=stats_file2,
                client_id="client2"
            )
            tracker2.record_usage(tokens_used=200)
            
            # Get aggregated stats
            aggregated = tracker1.get_aggregated_stats()
            
            assert len(aggregated) == 2
            assert str(stats_file1) in aggregated
            assert str(stats_file2) in aggregated
            assert aggregated[str(stats_file1)].total_tokens == 100
            assert aggregated[str(stats_file2)].total_tokens == 200
    
    def test_get_aggregated_stats_empty_directory(self):
        """Test getting aggregated stats from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            aggregated = tracker.get_aggregated_stats()
            assert len(aggregated) == 0
    
    def test_get_aggregated_stats_corrupted_files(self):
        """Test getting aggregated stats with corrupted files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_dir = Path(temp_dir)
            
            # Create valid stats file
            stats_file1 = stats_dir / "usage_valid.json"
            tracker1 = ThreadSafeUsageTracker(stats_file=stats_file1)
            tracker1.record_usage(tokens_used=100)
            
            # Create corrupted stats file
            corrupted_file = stats_dir / "usage_corrupted.json"
            corrupted_file.write_text("invalid json content")
            
            # Get aggregated stats (should skip corrupted file)
            aggregated = tracker1.get_aggregated_stats()
            
            assert len(aggregated) == 1
            assert str(stats_file1) in aggregated
    
    def test_thread_safety_record_usage(self):
        """Test thread safety when recording usage concurrently."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            def record_usage_worker():
                for _ in range(10):
                    tracker.record_usage(tokens_used=10)
            
            # Create multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=record_usage_worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check final stats
            stats = tracker.get_stats()
            assert stats.requests_today == 50  # 5 threads * 10 requests
            assert stats.tokens_used_today == 500  # 5 threads * 10 requests * 10 tokens
            assert stats.total_requests == 50
            assert stats.total_tokens == 500
    
    def test_thread_safety_get_stats(self):
        """Test thread safety when getting stats concurrently."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            def get_stats_worker():
                for _ in range(20):
                    stats = tracker.get_stats()
                    assert isinstance(stats, UsageStats)
            
            # Create multiple threads
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=get_stats_worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
    
    def test_file_creation_and_permissions(self):
        """Test that stats files are created with proper structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.PER_CLIENT,
                client_id="test_client"
            )
            
            # Check file was created
            assert stats_file.exists()
            
            # Check file content is valid JSON
            with open(stats_file) as f:
                data = json.load(f)
                assert isinstance(data, dict)
                assert "tokens_used_today" in data
                assert "client_id" in data
                assert data["client_id"] == "test_client"
    
    def test_load_stats_corrupted_file(self):
        """Test loading stats from corrupted file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            
            # Create corrupted file
            stats_file.write_text("invalid json")
            
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            # Should fall back to fresh stats
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 0
            assert stats.requests_today == 0
    
    def test_reset_if_new_day(self):
        """Test daily reset functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            # Record usage today
            tracker.record_usage(tokens_used=100)
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 100
            
            # Mock date change to tomorrow
            from datetime import date
            original_today = date.today
            tomorrow = date.fromordinal(original_today().toordinal() + 1)
            
            with patch('ai_utilities.usage_tracker.date') as mock_date:
                mock_date.today.return_value = tomorrow
                mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                
                # Getting stats should reset daily counters
                stats = tracker.get_stats()
                assert stats.tokens_used_today == 0
                assert stats.requests_today == 0
                assert stats.last_reset == tomorrow.isoformat()
                # Total should be preserved
                assert stats.total_tokens == 100
                assert stats.total_requests == 1
    
    def test_shared_locks_across_instances(self):
        """Test that multiple tracker instances share locks for same file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            
            tracker1 = ThreadSafeUsageTracker(stats_file=stats_file)
            tracker2 = ThreadSafeUsageTracker(stats_file=stats_file)
            
            # Should use the same lock
            assert tracker1._file_lock is tracker2._file_lock
    
    def test_backward_compatibility_alias(self):
        """Test that UsageTracker alias works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = UsageTracker(stats_file=stats_file)  # Using alias
            
            assert isinstance(tracker, ThreadSafeUsageTracker)
            tracker.record_usage(tokens_used=50)
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 50


class TestCreateUsageTracker:
    """Test the factory function."""
    
    def test_create_usage_tracker_with_enum_scope(self):
        """Test creating tracker with enum scope."""
        tracker = create_usage_tracker(
            scope=UsageScope.PER_CLIENT,
            client_id="test_client"
        )
        
        assert isinstance(tracker, ThreadSafeUsageTracker)
        assert tracker.scope == UsageScope.PER_CLIENT
        assert tracker.client_id == "test_client"
    
    def test_create_usage_tracker_with_string_scope(self):
        """Test creating tracker with string scope."""
        tracker = create_usage_tracker(
            scope="per_process",
            client_id="test_client"
        )
        
        assert isinstance(tracker, ThreadSafeUsageTracker)
        assert tracker.scope == UsageScope.PER_PROCESS
        assert tracker.client_id == "test_client"
    
    def test_create_usage_tracker_with_custom_file(self):
        """Test creating tracker with custom stats file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "custom_stats.json"
            
            tracker = create_usage_tracker(stats_file=stats_file)
            
            assert tracker.stats_file == stats_file
            assert stats_file.exists()
    
    def test_create_usage_tracker_default_scope(self):
        """Test creating tracker with default scope."""
        tracker = create_usage_tracker()
        
        assert isinstance(tracker, ThreadSafeUsageTracker)
        assert tracker.scope == UsageScope.PER_CLIENT


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_tracker_with_none_stats_file(self):
        """Test tracker with None stats file (should auto-generate)."""
        tracker = ThreadSafeUsageTracker()
        
        assert tracker.stats_file is not None
        assert tracker.stats_file.name.startswith("usage_")
        assert tracker.stats_file.suffix == ".json"
    
    def test_record_negative_tokens(self):
        """Test recording negative token usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            # Record positive usage first
            tracker.record_usage(tokens_used=100)
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 100
            
            # Record negative usage (should allow it)
            tracker.record_usage(tokens_used=-50)
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 50
    
    def test_large_token_numbers(self):
        """Test handling large token numbers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            large_number = 10**6
            tracker.record_usage(tokens_used=large_number)
            
            stats = tracker.get_stats()
            assert stats.tokens_used_today == large_number
            assert stats.total_tokens == large_number
    
    def test_concurrent_file_access_simulation(self):
        """Test simulation of concurrent file access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "test_stats.json"
            tracker = ThreadSafeUsageTracker(stats_file=stats_file)
            
            def concurrent_access_worker():
                try:
                    for i in range(5):
                        tracker.record_usage(tokens_used=i)
                        stats = tracker.get_stats()
                        assert stats.total_tokens >= 0
                except Exception as e:
                    pytest.fail(f"Concurrent access failed: {e}")
            
            # Run multiple threads
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=concurrent_access_worker)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Verify final state is consistent
            final_stats = tracker.get_stats()
            assert final_stats.requests_today == 15  # 3 threads * 5 requests
            assert final_stats.total_tokens == sum(range(5)) * 3  # 3 * (0+1+2+3+4)
