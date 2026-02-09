"""
test_coverage_usage_tracker.py

Additional tests for usage_tracker.py to improve coverage from 95% to 100%.
Focuses on the 7 missing lines.
"""

import os
import sys
import time
import tempfile
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.usage_tracker import ThreadSafeUsageTracker, UsageScope, UsageStats


class TestUsageTrackerCoverage:
    """Tests for usage_tracker.py coverage gaps."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.stats_file = Path(self.temp_dir) / "test_usage.json"
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_thread_safe_tracker_shared_locks_initialization(self):
        """Test ThreadSafeUsageTracker shared locks initialization (line 85)."""
        # Clear any existing shared locks
        if hasattr(ThreadSafeUsageTracker, '_shared_locks'):
            delattr(ThreadSafeUsageTracker, '_shared_locks')
        
        tracker = ThreadSafeUsageTracker(self.stats_file)
        
        # Should initialize shared locks dictionary
        assert hasattr(ThreadSafeUsageTracker, '_shared_locks')
        assert isinstance(ThreadSafeUsageTracker._shared_locks, dict)
        assert str(self.stats_file.absolute()) in ThreadSafeUsageTracker._shared_locks
    
        
    def test_thread_safe_tracker_multiple_instances_same_file(self):
        """Test multiple ThreadSafeUsageTracker instances share locks for same file."""
        tracker1 = ThreadSafeUsageTracker(self.stats_file)
        tracker2 = ThreadSafeUsageTracker(self.stats_file)
        
        # Both should use the same shared lock
        file_key = str(self.stats_file.absolute())
        assert tracker1._file_lock is tracker2._file_lock
        assert tracker1._file_lock is ThreadSafeUsageTracker._shared_locks[file_key]
    
    def test_thread_safe_tracker_different_files_different_locks(self):
        """Test ThreadSafeUsageTracker instances use different locks for different files."""
        stats_file2 = Path(self.temp_dir) / "test_usage2.json"
        
        tracker1 = ThreadSafeUsageTracker(self.stats_file)
        tracker2 = ThreadSafeUsageTracker(stats_file2)
        
        # Should use different locks for different files
        assert tracker1._file_lock is not tracker2._file_lock
