"""Tests for optional usage tracking functionality."""

import tempfile
import json
from pathlib import Path

from src.ai_utilities import AiClient, UsageTracker, UsageStats, create_usage_tracker, UsageScope
from tests.fake_provider import FakeProvider


def test_usage_tracker_basic():
    """Test basic usage tracking functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        stats_file = Path(temp_dir) / "test_stats.json"
        tracker = UsageTracker(stats_file)
        
        # Record some usage
        tracker.record_usage(100)
        tracker.record_usage(50)
        
        stats = tracker.get_stats()
        assert stats.tokens_used_today == 150
        assert stats.requests_today == 2
        assert stats.total_tokens == 150
        assert stats.total_requests == 2
        
        # Check file was created
        assert stats_file.exists()
        
        # Load and verify file contents
        with open(stats_file, 'r') as f:
            data = json.load(f)
            assert data['tokens_used_today'] == 150
            assert data['requests_today'] == 2


def test_usage_tracker_persistence():
    """Test that usage stats persist across tracker instances."""
    with tempfile.TemporaryDirectory() as temp_dir:
        stats_file = Path(temp_dir) / "test_stats.json"
        
        # First tracker instance
        tracker1 = UsageTracker(stats_file)
        tracker1.record_usage(100)
        
        # Second tracker instance should load previous stats
        tracker2 = UsageTracker(stats_file)
        stats = tracker2.get_stats()
        assert stats.tokens_used_today == 100
        assert stats.requests_today == 1


def test_ai_client_with_usage_tracking():
    """Test AiClient with usage tracking enabled."""
    fake_provider = FakeProvider()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        stats_file = Path(temp_dir) / "ai_usage.json"
        
        # Create client with usage tracking
        client = AiClient(provider=fake_provider, track_usage=True, usage_file=stats_file, auto_setup=False)
        
        # Make some requests
        response1 = client.ask("Test question 1")
        response2 = client.ask("Test question 2")
        
        # Check usage was tracked
        stats = client.get_usage_stats()
        assert stats is not None
        assert stats.requests_today == 2
        assert stats.total_tokens > 0  # Should have estimated tokens
        
        # Check file was created
        assert stats_file.exists()


def test_ai_client_without_usage_tracking():
    """Test AiClient without usage tracking (default)."""
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider, auto_setup=False)
    
    # Make request
    response = client.ask("Test question")
    
    # No usage tracking
    assert client.get_usage_stats() is None
    
    # Should not error when trying to print summary
    client.print_usage_summary()  # Should print "Usage tracking is not enabled."


def test_usage_tracker_daily_reset():
    """Test that daily stats reset when date changes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        stats_file = Path(temp_dir) / "test_stats.json"
        tracker = create_usage_tracker(stats_file=stats_file, scope=UsageScope.PER_CLIENT)
        
        # Record usage today
        tracker.record_usage(100)
        stats = tracker.get_stats()
        assert stats.tokens_used_today == 100
        
        # Manually modify the stats file to simulate new day
        from datetime import date, timedelta
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        # Read, modify, and write stats file directly
        import json
        with open(stats_file, 'r') as f:
            data = json.load(f)
        data['last_reset'] = yesterday
        with open(stats_file, 'w') as f:
            json.dump(data, f)
        
        # Create new tracker - should reset daily stats
        new_tracker = create_usage_tracker(stats_file=stats_file, scope=UsageScope.PER_CLIENT)
        new_stats = new_tracker.get_stats()
        assert new_stats.tokens_used_today == 0  # Reset for new day
        assert new_stats.total_tokens == 100   # Total preserved


def test_usage_tracker_print_summary(capsys):
    """Test usage tracker print summary."""
    with tempfile.TemporaryDirectory() as temp_dir:
        stats_file = Path(temp_dir) / "test_stats.json"
        tracker = create_usage_tracker(stats_file=stats_file, scope=UsageScope.PER_CLIENT)
        
        tracker.record_usage(100)
        tracker.print_summary()
        
        captured = capsys.readouterr()
        assert "AI Usage Summary (Scope: per_client):" in captured.out
        assert "Today: 100 tokens, 1 requests" in captured.out
        assert "Total: 100 tokens, 1 requests" in captured.out
