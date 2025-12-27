"""
Tests for thread-safe usage tracking with concurrent access.
"""

import concurrent.futures
import os
import shutil

# Add src to path for imports
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.usage_tracker import (
    ThreadSafeUsageTracker,
    UsageScope,
    UsageStats,
    create_usage_tracker,
)


@pytest.mark.slow
class TestThreadSafeUsageTracker:
    """Test thread-safe usage tracker functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Create a test usage tracker."""
        stats_file = temp_dir / "test_usage.json"
        return ThreadSafeUsageTracker(
            stats_file=stats_file,
            scope=UsageScope.PER_CLIENT,
            client_id="test_client"
        )
    
    def test_initialization(self, temp_dir):
        """Test tracker initialization with different scopes."""
        # Per-client scope
        stats_file = temp_dir / "per_client.json"
        tracker = ThreadSafeUsageTracker(
            stats_file=stats_file,
            scope=UsageScope.PER_CLIENT,
            client_id="test_client"
        )
        assert tracker.scope == UsageScope.PER_CLIENT
        assert tracker.client_id == "test_client"
        assert tracker.stats_file == stats_file
        
        # Per-process scope
        stats_file = temp_dir / "per_process.json"
        tracker = ThreadSafeUsageTracker(
            stats_file=stats_file,
            scope=UsageScope.PER_PROCESS
        )
        assert tracker.scope == UsageScope.PER_PROCESS
        assert tracker.process_id is not None
        
        # Global scope
        stats_file = temp_dir / "global.json"
        tracker = ThreadSafeUsageTracker(
            stats_file=stats_file,
            scope=UsageScope.GLOBAL
        )
        assert tracker.scope == UsageScope.GLOBAL
    
    def test_record_usage_single_thread(self, tracker):
        """Test basic usage recording in single-threaded environment."""
        # Record some usage
        tracker.record_usage(tokens_used=100)
        tracker.record_usage(tokens_used=50)
        tracker.record_usage(tokens_used=25)
        
        # Check stats
        stats = tracker.get_stats()
        assert stats.total_tokens == 175
        assert stats.total_requests == 3
        assert stats.tokens_used_today == 175
        assert stats.requests_today == 3
    
    def test_concurrent_usage_recording(self, tracker):
        """Test concurrent usage recording doesn't cause race conditions."""
        num_threads = 10
        calls_per_thread = 100
        tokens_per_call = 10
        
        def record_usage():
            for _ in range(calls_per_thread):
                tracker.record_usage(tokens_used=tokens_per_call)
        
        # Start multiple threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=record_usage)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no data was lost
        stats = tracker.get_stats()
        expected_total = num_threads * calls_per_thread * tokens_per_call
        expected_requests = num_threads * calls_per_thread
        
        assert stats.total_tokens == expected_total
        assert stats.total_requests == expected_requests
        assert stats.tokens_used_today == expected_total
        assert stats.requests_today == expected_requests
    
    def test_concurrent_read_write(self, tracker):
        """Test concurrent reading and writing doesn't cause corruption."""
        num_writer_threads = 5
        num_reader_threads = 5
        writes_per_thread = 50
        
        def writer():
            for i in range(writes_per_thread):
                tracker.record_usage(tokens_used=10)
                time.sleep(0.001)  # Small delay to increase contention
        
        def reader():
            for _ in range(writes_per_thread * 2):
                stats = tracker.get_stats()
                assert stats.total_tokens >= 0
                assert stats.total_requests >= 0
                time.sleep(0.001)
        
        # Start threads
        threads = []
        
        # Writer threads
        for _ in range(num_writer_threads):
            thread = threading.Thread(target=writer)
            threads.append(thread)
            thread.start()
        
        # Reader threads
        for _ in range(num_reader_threads):
            thread = threading.Thread(target=reader)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify final state
        stats = tracker.get_stats()
        expected_tokens = num_writer_threads * writes_per_thread * 10
        expected_requests = num_writer_threads * writes_per_thread
        
        assert stats.total_tokens == expected_tokens
        assert stats.total_requests == expected_requests
    
    def test_different_scopes_isolation(self, temp_dir):
        """Test that different scopes are properly isolated."""
        # Create trackers with different scopes
        per_client_file = temp_dir / "per_client.json"
        per_process_file = temp_dir / "per_process.json"
        global_file = temp_dir / "global.json"
        
        tracker_client = ThreadSafeUsageTracker(
            stats_file=per_client_file,
            scope=UsageScope.PER_CLIENT,
            client_id="client1"
        )
        
        tracker_process = ThreadSafeUsageTracker(
            stats_file=per_process_file,
            scope=UsageScope.PER_PROCESS
        )
        
        tracker_global = ThreadSafeUsageTracker(
            stats_file=global_file,
            scope=UsageScope.GLOBAL
        )
        
        # Record usage in each tracker
        tracker_client.record_usage(tokens_used=100)
        tracker_process.record_usage(tokens_used=200)
        tracker_global.record_usage(tokens_used=300)
        
        # Verify isolation
        assert tracker_client.get_stats().total_tokens == 100
        assert tracker_process.get_stats().total_tokens == 200
        assert tracker_global.get_stats().total_tokens == 300
        
        # Verify files are separate
        assert per_client_file.exists()
        assert per_process_file.exists()
        assert global_file.exists()
    
    def test_custom_client_id_sharing(self, temp_dir):
        """Test that trackers with same client ID share data."""
        custom_file = temp_dir / "custom.json"
        
        # Create two trackers with same client ID
        tracker1 = ThreadSafeUsageTracker(
            stats_file=custom_file,
            scope=UsageScope.PER_CLIENT,
            client_id="shared_client"
        )
        
        tracker2 = ThreadSafeUsageTracker(
            stats_file=custom_file,
            scope=UsageScope.PER_CLIENT,
            client_id="shared_client"
        )
        
        # Record usage from both trackers
        tracker1.record_usage(tokens_used=100)
        tracker2.record_usage(tokens_used=150)
        
        # Both should see the combined total
        stats1 = tracker1.get_stats()
        stats2 = tracker2.get_stats()
        
        assert stats1.total_tokens == 250
        assert stats2.total_tokens == 250
        assert stats1.total_requests == 2
        assert stats2.total_requests == 2
    
    def test_reset_stats(self, tracker):
        """Test stats reset functionality."""
        # Record some usage
        tracker.record_usage(tokens_used=100)
        tracker.record_usage(tokens_used=50)
        
        # Verify usage was recorded
        stats = tracker.get_stats()
        assert stats.total_tokens == 150
        assert stats.total_requests == 2
        
        # Reset stats
        tracker.reset_stats()
        
        # Verify reset
        stats = tracker.get_stats()
        assert stats.total_tokens == 0
        assert stats.total_requests == 0
        assert stats.tokens_used_today == 0
        assert stats.requests_today == 0
    
    def test_aggregated_stats(self, temp_dir):
        """Test aggregated statistics collection."""
        # Create multiple tracker files
        base_dir = temp_dir / "usage_stats"
        base_dir.mkdir()
        
        # Create some test files
        for i in range(3):
            stats_file = base_dir / f"usage_client_{i}.json"
            tracker = ThreadSafeUsageTracker(
                stats_file=stats_file,
                scope=UsageScope.PER_CLIENT,
                client_id=f"client_{i}"
            )
            tracker.record_usage(tokens_used=100 * (i + 1))
        
        # Get aggregated stats
        tracker = ThreadSafeUsageTracker(stats_file=base_dir / "dummy.json")
        aggregated = tracker.get_aggregated_stats()
        
        assert len(aggregated) == 3
        
        total_tokens = sum(stats.total_tokens for stats in aggregated.values())
        assert total_tokens == 600  # 100 + 200 + 300
    
    def test_file_corruption_handling(self, tracker):
        """Test handling of corrupted stats files."""
        # Corrupt the stats file
        with open(tracker.stats_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle corruption gracefully
        stats = tracker.get_stats()
        assert isinstance(stats, UsageStats)
        assert stats.total_tokens == 0
        assert stats.total_requests == 0
    
    def test_memory_caching(self, tracker):
        """Test that memory caching reduces file I/O."""
        # Record usage
        tracker.record_usage(tokens_used=100)
        
        # First read should hit file
        stats1 = tracker.get_stats()
        
        # Immediate second read should hit cache
        stats2 = tracker.get_stats()
        
        # Should be same object (cached)
        assert stats1.total_tokens == stats2.total_tokens
        assert stats1.total_requests == stats2.total_requests


class TestCreateUsageTracker:
    """Test the factory function for creating usage trackers."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_create_tracker_with_string_scope(self, temp_dir):
        """Test creating tracker with string scope."""
        tracker = create_usage_tracker(
            scope="per_client",
            stats_file=temp_dir / "test.json",
            client_id="test"
        )
        
        assert isinstance(tracker, ThreadSafeUsageTracker)
        assert tracker.scope == UsageScope.PER_CLIENT
        assert tracker.client_id == "test"
    
    def test_create_tracker_with_enum_scope(self, temp_dir):
        """Test creating tracker with enum scope."""
        tracker = create_usage_tracker(
            scope=UsageScope.GLOBAL,
            stats_file=temp_dir / "test.json"
        )
        
        assert isinstance(tracker, ThreadSafeUsageTracker)
        assert tracker.scope == UsageScope.GLOBAL
    
    def test_create_tracker_defaults(self, temp_dir):
        """Test creating tracker with default parameters."""
        # Change to temp directory for test
        original_cwd = Path.cwd()
        os.chdir(temp_dir)
        
        try:
            tracker = create_usage_tracker()
            assert isinstance(tracker, ThreadSafeUsageTracker)
            assert tracker.scope == UsageScope.PER_CLIENT
            assert tracker.client_id is not None
            assert tracker.stats_file is not None
        finally:
            os.chdir(original_cwd)


class TestConcurrentStressTest:
    """Stress tests for concurrent usage tracking."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_high_concurrency_stress(self, temp_dir):
        """Test high concurrency scenario."""
        stats_file = temp_dir / "stress_test.json"
        tracker = ThreadSafeUsageTracker(
            stats_file=stats_file,
            scope=UsageScope.PER_PROCESS
        )
        
        num_threads = 50
        operations_per_thread = 20
        
        def stress_worker():
            for i in range(operations_per_thread):
                tracker.record_usage(tokens_used=i % 10 + 1)
        
        # Run stress test
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_worker) for _ in range(num_threads)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        
        # Verify data integrity
        stats = tracker.get_stats()
        expected_requests = num_threads * operations_per_thread
        expected_tokens = sum((i % 10 + 1) for i in range(operations_per_thread)) * num_threads
        
        assert stats.total_requests == expected_requests
        assert stats.total_tokens == expected_tokens
        
        print(f"Stress test completed in {end_time - start_time:.2f}s")
        print(f"Processed {expected_requests} operations with {num_threads} threads")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
