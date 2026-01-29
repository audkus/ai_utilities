"""Tests for rate_limiter.py module."""

import json
import pytest
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from ai_utilities.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def rate_limiter(self, temp_config_dir):
        """Create RateLimiter instance for testing."""
        config_path = Path(temp_config_dir) / "config.json"
        return RateLimiter(
            module_name="test-model",
            rpm=10,  # 10 requests per minute
            tpm=1000,  # 1000 tokens per minute
            tpd=10000,  # 10000 tokens per day
            config_path=str(config_path)
        )
    
    def test_initialization(self, temp_config_dir):
        """Test RateLimiter initialization."""
        config_path = Path(temp_config_dir) / "config.json"
        
        limiter = RateLimiter(
            module_name="test-model",
            rpm=60,
            tpm=5000,
            tpd=50000,
            config_path=str(config_path)
        )
        
        assert limiter.module_name == "test-model"
        assert limiter.rpm == 60
        assert limiter.tpm == 5000
        assert limiter.tpd == 50000
        assert limiter.requests_made == 0
        assert limiter.tokens_used == 0
        assert limiter.tokens_used_today == 0
        assert limiter.ai_stats_file == str(Path(temp_config_dir) / "ai_statistics.json")
        assert isinstance(limiter.lock, type(threading.Lock()))
    
    def test_load_stats_no_file(self, temp_config_dir):
        """Test loading stats when no stats file exists."""
        config_path = Path(temp_config_dir) / "config.json"
        
        limiter = RateLimiter(
            module_name="test-model",
            rpm=10,
            tpm=1000,
            tpd=10000,
            config_path=str(config_path)
        )
        
        # Should initialize with default values
        assert limiter.tokens_used_today == 0
        assert limiter.last_reset is not None
    
    def test_load_stats_existing_file(self, temp_config_dir):
        """Test loading stats from existing file."""
        config_path = Path(temp_config_dir) / "config.json"
        stats_file = Path(temp_config_dir) / "ai_statistics.json"
        
        # Create existing stats file
        existing_stats = {
            "tokens_used_today": 500,
            "last_reset": datetime.now().isoformat(),
            "module_name": "existing-model",
            "max_limits": {"tpd": 20000}
        }
        
        with open(stats_file, 'w') as f:
            json.dump(existing_stats, f)
        
        limiter = RateLimiter(
            module_name="test-model",
            rpm=10,
            tpm=1000,
            tpd=10000,
            config_path=str(config_path)
        )
        
        assert limiter.tokens_used_today == 500
        assert limiter.last_reset is not None
    
    def test_load_stats_invalid_json(self, temp_config_dir):
        """Test loading stats with invalid JSON."""
        config_path = Path(temp_config_dir) / "config.json"
        stats_file = Path(temp_config_dir) / "ai_statistics.json"
        
        # Create invalid JSON file
        with open(stats_file, 'w') as f:
            f.write("invalid json")
        
        # Should handle gracefully and create new file
        limiter = RateLimiter(
            module_name="test-model",
            rpm=10,
            tpm=1000,
            tpd=10000,
            config_path=str(config_path)
        )
        
        assert limiter.tokens_used_today == 0
    
    def test_save_stats(self, rate_limiter, temp_config_dir):
        """Test saving stats to file."""
        rate_limiter.tokens_used_today = 1500
        rate_limiter.last_reset = datetime.now()
        
        rate_limiter.save_stats()
        
        stats_file = Path(temp_config_dir) / "ai_statistics.json"
        assert stats_file.exists()
        
        with open(stats_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["tokens_used_today"] == 1500
        assert saved_data["module_name"] == "test-model"
        assert saved_data["max_limits"]["tpd"] == 10000
    
    def test_save_stats_custom_data(self, rate_limiter, temp_config_dir):
        """Test saving custom stats data."""
        custom_data = {
            "tokens_used_today": 999,
            "last_reset": datetime.now().isoformat(),
            "custom_field": "test"
        }
        
        rate_limiter.save_stats(custom_data)
        
        stats_file = Path(temp_config_dir) / "ai_statistics.json"
        with open(stats_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["tokens_used_today"] == 999
        assert saved_data["custom_field"] == "test"
    
    def test_reset_daily_usage(self, rate_limiter):
        """Test resetting daily usage."""
        rate_limiter.tokens_used_today = 5000
        old_reset_time = rate_limiter.last_reset
        
        time.sleep(0.01)  # Small delay to ensure different timestamp
        rate_limiter.reset_daily_usage()
        
        assert rate_limiter.tokens_used_today == 0
        assert rate_limiter.last_reset > old_reset_time
    
    def test_check_reset_same_day(self, rate_limiter):
        """Test check_reset when same day."""
        rate_limiter.tokens_used_today = 1000
        original_last_reset = rate_limiter.last_reset
        
        rate_limiter.check_reset()
        
        # Should not reset since it's same day
        assert rate_limiter.tokens_used_today == 1000
        assert rate_limiter.last_reset == original_last_reset
    
    def test_check_reset_new_day(self, rate_limiter):
        """Test check_reset when new day."""
        rate_limiter.tokens_used_today = 1000
        
        # Mock datetime.now() to return next day
        tomorrow = datetime.now() + timedelta(days=1)
        with patch('ai_utilities.rate_limiter.datetime') as mock_datetime:
            mock_datetime.now.return_value = tomorrow
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            rate_limiter.check_reset()
            
            # Should reset since it's new day
            assert rate_limiter.tokens_used_today == 0
    
    def test_can_proceed_within_limits(self, rate_limiter):
        """Test can_proceed when within all limits."""
        rate_limiter.requests_made = 5
        rate_limiter.tokens_used = 500
        
        result = rate_limiter.can_proceed(100)
        
        assert result is True  # Within all limits
    
    def test_can_proceed_exceeds_rpm(self, rate_limiter):
        """Test can_proceed when exceeding RPM."""
        rate_limiter.requests_made = 10  # At limit
        
        result = rate_limiter.can_proceed(100)
        
        assert result is False  # Exceeds RPM
    
    def test_can_proceed_exceeds_tpm(self, rate_limiter):
        """Test can_proceed when exceeding TPM."""
        rate_limiter.requests_made = 5
        rate_limiter.tokens_used = 950
        
        result = rate_limiter.can_proceed(100)  # Would make 1050 > 1000
        
        assert result is False  # Exceeds TPM
    
    def test_can_proceed_exceeds_tpd(self, rate_limiter):
        """Test can_proceed when exceeding TPD."""
        rate_limiter.tokens_used_today = 9500
        
        result = rate_limiter.can_proceed(1000)  # Would make 10500 > 10000
        
        assert result is False  # Exceeds TPD
    
    def test_can_proceed_zero_tokens(self, rate_limiter):
        """Test can_proceed with zero tokens."""
        rate_limiter.requests_made = 5
        
        result = rate_limiter.can_proceed(0)
        
        assert result is True  # Zero tokens should always be allowed if within RPM
    
    def test_record_usage(self, rate_limiter):
        """Test recording usage."""
        initial_requests = rate_limiter.requests_made
        initial_tokens = rate_limiter.tokens_used
        initial_daily_tokens = rate_limiter.tokens_used_today
        
        rate_limiter.record_usage(150)
        
        assert rate_limiter.requests_made == initial_requests + 1
        assert rate_limiter.tokens_used == initial_tokens + 150
        assert rate_limiter.tokens_used_today == initial_daily_tokens + 150
    
    def test_reset_minute_counters(self, rate_limiter):
        """Test resetting minute counters."""
        rate_limiter.requests_made = 8
        rate_limiter.tokens_used = 800
        
        rate_limiter.reset_minute_counters()
        
        assert rate_limiter.requests_made == 0
        assert rate_limiter.tokens_used == 0
        # Daily counter should remain unchanged
        assert rate_limiter.tokens_used_today >= 0
    
    def test_thread_safety_can_proceed(self, rate_limiter):
        """Test thread safety of can_proceed method."""
        results = []
        
        def check_can_proceed():
            for _ in range(10):
                result = rate_limiter.can_proceed(50)
                results.append(result)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=check_can_proceed)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have completed without errors
        assert len(results) == 50
    
    def test_thread_safety_record_usage(self, rate_limiter):
        """Test thread safety of record_usage method."""
        
        def record_usage():
            for _ in range(10):
                rate_limiter.record_usage(10)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_usage)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have recorded all usage correctly
        assert rate_limiter.requests_made == 50
        assert rate_limiter.tokens_used == 500
        assert rate_limiter.tokens_used_today == 500
    
    def test_start_reset_timer(self, rate_limiter):
        """Test starting reset timer."""
        # This test is tricky because the timer runs in background
        # We'll just test that it starts without error
        rate_limiter.start_reset_timer()
        
        # Give it a moment to start
        time.sleep(0.1)
        
        # Should not raise any exceptions
        assert True
    
    def test_integration_workflow(self, rate_limiter):
        """Test complete workflow of rate limiting."""
        # Should be able to make requests within limits
        assert rate_limiter.can_proceed(100) is True
        rate_limiter.record_usage(100)
        
        assert rate_limiter.can_proceed(200) is True
        rate_limiter.record_usage(200)
        
        # Check counters
        assert rate_limiter.requests_made == 2
        assert rate_limiter.tokens_used == 300
        assert rate_limiter.tokens_used_today == 300
        
        # Reset minute counters
        rate_limiter.reset_minute_counters()
        assert rate_limiter.requests_made == 0
        assert rate_limiter.tokens_used == 0
        assert rate_limiter.tokens_used_today == 300  # Daily should remain


class TestRateLimiterEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def rate_limiter_zero_limits(self, temp_config_dir):
        """Create RateLimiter with zero limits."""
        config_path = Path(temp_config_dir) / "config.json"
        return RateLimiter(
            module_name="test-model",
            rpm=0,
            tpm=0,
            tpd=0,
            config_path=str(config_path)
        )
    
    @pytest.fixture
    def rate_limiter(self, temp_config_dir):
        """Create RateLimiter instance for testing."""
        config_path = Path(temp_config_dir) / "config.json"
        return RateLimiter(
            module_name="test-model",
            rpm=10,  # 10 requests per minute
            tpm=1000,  # 1000 tokens per minute
            tpd=10000,  # 10000 tokens per day
            config_path=str(config_path)
        )
    
    def test_zero_limits(self, rate_limiter_zero_limits):
        """Test behavior with zero limits."""
        # Should not be able to proceed with any tokens
        assert rate_limiter_zero_limits.can_proceed(1) is False
        assert rate_limiter_zero_limits.can_proceed(0) is False  # Even zero tokens due to RPM=0
    
    def test_negative_tokens(self, rate_limiter):
        """Test behavior with negative tokens."""
        # Negative tokens should be treated as zero (can proceed if within other limits)
        result = rate_limiter.can_proceed(-10)
        assert result is True  # Negative tokens should not limit
    
    def test_large_token_count(self, rate_limiter):
        """Test behavior with very large token count."""
        result = rate_limiter.can_proceed(1000000)
        assert result is False  # Should exceed limits
    
    def test_file_permission_error_on_save(self, rate_limiter):
        """Test handling of file permission errors when saving."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should not raise exception
            rate_limiter.save_stats()
    
    def test_file_permission_error_on_load(self, temp_config_dir):
        """Test handling of file permission errors when loading."""
        config_path = Path(temp_config_dir) / "config.json"
        stats_file = Path(temp_config_dir) / "ai_statistics.json"
        
        # Create file
        with open(stats_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should handle gracefully and create new stats
            limiter = RateLimiter(
                module_name="test-model",
                rpm=10,
                tpm=1000,
                tpd=10000,
                config_path=str(config_path)
            )
            
            assert limiter.tokens_used_today == 0
    
    def test_concurrent_can_proceed_and_record(self, rate_limiter):
        """Test concurrent can_proceed and record_usage calls."""
        results = []
        
        def worker():
            if rate_limiter.can_proceed(50):
                rate_limiter.record_usage(50)
                results.append(True)
            else:
                results.append(False)
        
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have some successes and some failures
        assert len(results) == 20
        assert any(results)  # At least some should succeed
        assert not all(results)  # Not all should succeed due to limits
