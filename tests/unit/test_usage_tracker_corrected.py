"""Corrected extended tests for usage_tracker.py based on actual API."""

import pytest
import json
import threading
import time
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Optional

from ai_utilities.usage_tracker import (
    UsageScope, UsageStats, ThreadSafeUsageTracker, UsageTracker, create_usage_tracker
)


class TestUsageTrackerCorrected:
    """Corrected test cases for usage tracker based on actual API."""

    def test_usage_scope_enum_values(self):
        """Test UsageScope enum values."""
        assert UsageScope.PER_CLIENT.value == "per_client"
        assert UsageScope.PER_PROCESS.value == "per_process"
        assert UsageScope.GLOBAL.value == "global"

    def test_usage_stats_model_validation(self):
        """Test UsageStats Pydantic model validation."""
        # Test with all fields
        stats = UsageStats(
            tokens_used_today=1000,
            requests_today=50,
            last_reset=date.today().isoformat(),
            total_tokens=10000,
            total_requests=500,
            client_id="test-client",
            process_id=12345
        )
        
        assert stats.tokens_used_today == 1000
        assert stats.requests_today == 50
        assert stats.last_reset == date.today().isoformat()
        assert stats.total_tokens == 10000
        assert stats.total_requests == 500
        assert stats.client_id == "test-client"
        assert stats.process_id == 12345

    def test_usage_stats_defaults(self):
        """Test UsageStats default values."""
        stats = UsageStats()
        
        assert stats.tokens_used_today == 0
        assert stats.requests_today == 0
        assert stats.last_reset == date.today().isoformat()
        assert stats.total_tokens == 0
        assert stats.total_requests == 0
        assert stats.client_id is None
        assert stats.process_id is None

    def test_thread_safe_usage_tracker_per_client_scope(self):
        """Test ThreadSafeUsageTracker with per_client scope."""
        client_id = "test-client-123"
        tracker = ThreadSafeUsageTracker(
            scope=UsageScope.PER_CLIENT,
            client_id=client_id
        )
        
        assert tracker.scope == UsageScope.PER_CLIENT
        assert tracker.client_id == client_id

    def test_thread_safe_usage_tracker_per_process_scope(self):
        """Test ThreadSafeUsageTracker with per_process scope."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
        
        assert tracker.scope == UsageScope.PER_PROCESS
        assert tracker.client_id is not None  # Auto-generated
        assert tracker.process_id is not None

    def test_thread_safe_usage_tracker_global_scope(self):
        """Test ThreadSafeUsageTracker with global scope."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.GLOBAL)
        
        assert tracker.scope == UsageScope.GLOBAL
        assert tracker.client_id is not None  # Auto-generated
        assert tracker.process_id is not None

    def test_record_usage_basic(self):
        """Test basic usage recording with actual API."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Record some usage - actual API only takes tokens_used
        tracker.record_usage(tokens_used=100)
        
        stats = tracker.get_stats()
        assert stats.tokens_used_today == 100
        assert stats.requests_today == 1
        assert stats.total_tokens == 100
        assert stats.total_requests == 1

    def test_record_usage_multiple_calls(self):
        """Test recording multiple usage calls."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Record multiple usage events
        tracker.record_usage(tokens_used=50)
        tracker.record_usage(tokens_used=75)
        tracker.record_usage(tokens_used=25)
        
        stats = tracker.get_stats()
        assert stats.tokens_used_today == 150
        assert stats.requests_today == 3
        assert stats.total_tokens == 150
        assert stats.total_requests == 3

    def test_record_usage_zero_values(self):
        """Test recording zero usage values."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Record zero usage (should increment requests but not tokens)
        tracker.record_usage(tokens_used=0)
        
        stats = tracker.get_stats()
        assert stats.tokens_used_today == 0
        assert stats.requests_today == 1
        assert stats.total_tokens == 0
        assert stats.total_requests == 1

    def test_record_usage_large_values(self):
        """Test recording large usage values."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Record large values
        large_tokens = 1000000
        tracker.record_usage(tokens_used=large_tokens)
        
        stats = tracker.get_stats()
        assert stats.tokens_used_today == large_tokens
        assert stats.requests_today == 1
        assert stats.total_tokens == large_tokens
        assert stats.total_requests == 1

    def test_thread_safe_concurrent_tracking(self):
        """Test thread-safe concurrent usage tracking."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
        results = []
        
        def worker_thread(thread_id):
            for i in range(10):  # Reduced iterations for faster test
                tracker.record_usage(tokens_used=1)
            results.append(thread_id)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed
        assert len(results) == 5
        
        # Verify usage was tracked correctly
        stats = tracker.get_stats()
        assert stats.tokens_used_today == 50  # 5 threads * 10 tokens each
        assert stats.requests_today == 50   # 5 threads * 10 requests each

    def test_get_stats_with_file_persistence(self):
        """Test getting stats with file persistence using real file operations."""
        import tempfile
        import json
        from pathlib import Path
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a stats file with test data
            stats_file = Path(temp_dir) / "usage_test-client.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            test_data = {
                "tokens_used_today": 200,
                "requests_today": 10,
                "last_reset": date.today().isoformat(),
                "total_tokens": 2000,
                "total_requests": 100,
                "client_id": "test-client"
            }
            
            with open(stats_file, 'w') as f:
                json.dump(test_data, f)
            
            # Create tracker with the existing stats file
            tracker = ThreadSafeUsageTracker(
                scope=UsageScope.PER_CLIENT,
                client_id="test-client",
                stats_file=stats_file
            )
            
            # Test contract: stats should be loaded from file
            stats = tracker.get_stats()
            assert stats.tokens_used_today == 200
            assert stats.requests_today == 10
            assert stats.total_tokens == 2000
            assert stats.total_requests == 100
            assert stats.client_id == "test-client"

    def test_reset_stats(self):
        """Test reset_stats method."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Record some usage
        tracker.record_usage(tokens_used=150)
        
        # Verify stats exist
        stats_before = tracker.get_stats()
        assert stats_before.tokens_used_today == 150
        assert stats_before.requests_today == 1
        
        # Reset stats
        tracker.reset_stats()
        
        # Verify stats are reset
        stats_after = tracker.get_stats()
        assert stats_after.tokens_used_today == 0
        assert stats_after.requests_today == 0
        assert stats_after.total_tokens == 0
        assert stats_after.total_requests == 0

    def test_print_summary(self):
        """Test print_summary method."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Record some usage
        tracker.record_usage(tokens_used=100)
        
        # Test print_summary (should not raise exception)
        with patch('builtins.print') as mock_print:
            tracker.print_summary()
            
            # Verify print was called
            assert mock_print.call_count > 0

    def test_get_aggregated_stats(self):
        """Test get_aggregated_stats method using real files."""
        import tempfile
        import json
        from pathlib import Path
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_dir = Path(temp_dir) / ".ai_utilities" / "usage_stats"
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            # Create multiple stats files
            client1_data = {
                "tokens_used_today": 100,
                "requests_today": 5,
                "total_tokens": 1000,
                "total_requests": 50,
                "client_id": "client1"
            }
            
            client2_data = {
                "tokens_used_today": 200,
                "requests_today": 10,
                "total_tokens": 2000,
                "total_requests": 100,
                "client_id": "client2"
            }
            
            # Write stats files
            with open(stats_dir / "usage_client1.json", 'w') as f:
                json.dump(client1_data, f)
            
            with open(stats_dir / "usage_client2.json", 'w') as f:
                json.dump(client2_data, f)
            
            # Create tracker pointing to the temp directory
            tracker = ThreadSafeUsageTracker(
                scope=UsageScope.PER_CLIENT,
                client_id="test",
                stats_file=stats_dir / "usage_test.json"
            )
            
            # Test contract: should aggregate stats from all files
            aggregated = tracker.get_aggregated_stats()
            
            # Should include all 3 files (client1, client2, and test)
            assert len(aggregated) == 3
            assert any("client1" in path for path in aggregated.keys())
            assert any("client2" in path for path in aggregated.keys())
            assert any("test" in path for path in aggregated.keys())
            
            # Verify aggregated data
            for stats in aggregated.values():
                if stats.client_id == "client1":
                    assert stats.tokens_used_today == 100
                    assert stats.requests_today == 5
                elif stats.client_id == "client2":
                    assert stats.tokens_used_today == 200
                    assert stats.requests_today == 10
                elif stats.client_id == "test":
                    # Test tracker's own stats (should be empty/new)
                    assert stats.tokens_used_today == 0
                    assert stats.requests_today == 0

    def test_create_usage_tracker_factory_function(self):
        """Test create_usage_tracker factory function."""
        # Test with string scope
        tracker1 = create_usage_tracker(scope="per_client", client_id="test-client")
        assert tracker1.scope == UsageScope.PER_CLIENT
        assert tracker1.client_id == "test-client"
        
        # Test with enum scope
        tracker2 = create_usage_tracker(scope=UsageScope.GLOBAL)
        assert tracker2.scope == UsageScope.GLOBAL
        
        # Test with custom stats file
        custom_file = Path("/tmp/custom_usage.json")
        tracker3 = create_usage_tracker(stats_file=custom_file)
        assert tracker3.stats_file == custom_file

    def test_auto_daily_reset(self):
        """Test automatic daily reset when date changes."""
        import tempfile
        import json
        from pathlib import Path
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            stats_file = Path(temp_dir) / "usage_test.json"
            
            # Create stats with yesterday's date
            yesterday = date.today() - timedelta(days=1)
            old_stats = UsageStats(
                tokens_used_today=100,
                requests_today=5,
                last_reset=yesterday.isoformat(),
                total_tokens=100,
                total_requests=5,
                client_id="test"
            )
            
            # Write old stats to file
            with open(stats_file, 'w') as f:
                json.dump(old_stats.model_dump(), f)
            
            # Create tracker with the existing stats file
            tracker = ThreadSafeUsageTracker(
                scope=UsageScope.PER_CLIENT,
                client_id="test",
                stats_file=stats_file
            )
            
            # Test contract: stats should be reset when getting stats today
            stats = tracker.get_stats()
            
            # Daily stats should be reset (it's a new day)
            assert stats.tokens_used_today == 0
            assert stats.requests_today == 0
            assert stats.last_reset == date.today().isoformat()
            
            # Total stats should be preserved
            assert stats.total_tokens == 100
            assert stats.total_requests == 5
            assert stats.client_id == "test"

    def test_process_id_assignment(self):
        """Test process ID assignment for different scopes."""
        import os
        
        # Test per_process scope
        tracker1 = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
        assert tracker1.process_id == os.getpid()
        
        # Test per_client scope (should have process_id for file naming)
        tracker2 = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        assert tracker2.process_id == os.getpid()
        
        # Test global scope (should have process_id for file naming)
        tracker3 = ThreadSafeUsageTracker(scope=UsageScope.GLOBAL)
        assert tracker3.process_id == os.getpid()

    def test_client_id_validation(self):
        """Test client ID validation for different scopes."""
        # Test per_client scope with client_id
        tracker1 = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test-client")
        assert tracker1.client_id == "test-client"
        
        # Test per_client scope without client_id (should auto-generate)
        tracker2 = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT)
        assert tracker2.client_id is not None
        assert len(tracker2.client_id) > 0
        assert tracker2.client_id.startswith("client_")
        
        # Test per_process scope (should auto-generate client_id)
        tracker3 = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
        assert tracker3.client_id is not None
        assert len(tracker3.client_id) > 0
        
        # Test global scope (should auto-generate client_id)
        tracker4 = ThreadSafeUsageTracker(scope=UsageScope.GLOBAL)
        assert tracker4.client_id is not None
        assert len(tracker4.client_id) > 0

    def test_shared_locks_thread_safety(self):
        """Test shared locks dictionary thread safety."""
        # This tests the class-level shared locks
        tracker1 = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
        tracker2 = ThreadSafeUsageTracker(scope=UsageScope.PER_PROCESS)
        
        # Both should use the same shared lock for per_process scope
        assert hasattr(ThreadSafeUsageTracker, '_shared_locks')
        assert len(ThreadSafeUsageTracker._shared_locks) > 0

    def test_backward_compatibility_alias(self):
        """Test backward compatibility alias."""
        
        # UsageTracker should be an alias for ThreadSafeUsageTracker
        assert UsageTracker == ThreadSafeUsageTracker
        
        # Should be able to create instances with the alias
        tracker = UsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        assert isinstance(tracker, ThreadSafeUsageTracker)

    def test_negative_usage_tracking(self):
        """Test tracking negative usage values."""
        tracker = ThreadSafeUsageTracker(scope=UsageScope.PER_CLIENT, client_id="test")
        
        # Negative values should be allowed (business logic might validate elsewhere)
        tracker.record_usage(tokens_used=-10)
        
        stats = tracker.get_stats()
        assert stats.tokens_used_today == -10
        assert stats.requests_today == 1

    def test_usage_stats_model_with_negative_data(self):
        """Test UsageStats model with negative data."""
        # Test with negative values (should be allowed in model)
        stats = UsageStats(
            tokens_used_today=-10,
            requests_today=-5,
            total_tokens=-100,
            total_requests=-50
        )
        
        # Model should accept negative values
        assert stats.tokens_used_today == -10
        assert stats.requests_today == -5
        assert stats.total_tokens == -100
        assert stats.total_requests == -50
