"""Tests for progress indicator functionality."""

import time
from unittest.mock import patch

from src.ai_utilities import AiClient
from src.ai_utilities.progress_indicator import ProgressIndicator
from tests.fake_provider import FakeProvider


def test_progress_indicator_enabled_by_default():
    """Test that progress indicator is enabled by default."""
    from src.ai_utilities import AiSettings
    settings = AiSettings(api_key="test-key-for-testing")
    client = AiClient(settings, auto_setup=False)
    assert client.show_progress is True


def test_progress_indicator_can_be_disabled():
    """Test that progress indicator can be disabled."""
    from src.ai_utilities import AiSettings
    settings = AiSettings(api_key="test-key-for-testing")
    client = AiClient(settings, show_progress=False, auto_setup=False)
    assert client.show_progress is False


def test_progress_indicator_context_manager():
    """Test progress indicator context manager functionality."""
    with patch('sys.stdout') as mock_stdout:
        indicator = ProgressIndicator(show=True)
        
        with indicator:
            # Simulate some work
            time.sleep(0.1)
        
        # Should have written to stdout
        mock_stdout.write.assert_called()


def test_progress_indicator_disabled():
    """Test progress indicator when disabled."""
    with patch('sys.stdout') as mock_stdout:
        indicator = ProgressIndicator(show=False)
        
        with indicator:
            # Simulate some work
            time.sleep(0.1)
        
        # Should not have written to stdout
        mock_stdout.write.assert_not_called()


def test_ai_client_with_progress_indicator(capsys):
    """Test AiClient with progress indicator enabled."""
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider, show_progress=True, auto_setup=False)
    
    # Make a request
    response = client.ask("Test question")
    
    # Should have some progress output
    captured = capsys.readouterr()
    assert "Waiting for AI response" in captured.out
    assert "completed in" in captured.out


def test_ai_client_without_progress_indicator(capsys):
    """Test AiClient with progress indicator disabled."""
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider, show_progress=False, auto_setup=False)
    
    # Make a request
    response = client.ask("Test question")
    
    # Should not have progress output
    captured = capsys.readouterr()
    assert "Waiting for AI response" not in captured.out
    assert "completed in" not in captured.out


def test_progress_indicator_timing_format():
    """Test that progress indicator shows correct time format."""
    with patch('sys.stdout') as mock_stdout:
        indicator = ProgressIndicator(show=True)
        
        with indicator:
            # Sleep for a short time to ensure some elapsed time
            time.sleep(0.1)
        
        # Should have written to stdout with time format
        mock_stdout.write.assert_called()
        
        # Check that the completion message contains time format
        calls = [str(call) for call in mock_stdout.write.call_args_list]
        completion_message = any("completed in [" in call for call in calls)
        assert completion_message, f"Expected 'completed in [' in output, got: {calls}"


def test_progress_indicator_displays_time():
    """Test that progress indicator actually displays elapsed time."""
    with patch('sys.stdout') as mock_stdout:
        indicator = ProgressIndicator(show=True)
        
        with indicator:
            # Sleep briefly to ensure elapsed time
            time.sleep(0.1)
        
        # Should show completion message with time
        calls = [str(call) for call in mock_stdout.write.call_args_list]
        has_time_format = any("completed in [00:00:" in call for call in calls)
        assert has_time_format, f"Expected time format in output, got: {calls}"


def test_progress_indicator_enable_disable():
    """Test enabling and disabling progress indicator."""
    indicator = ProgressIndicator(show=True)
    assert indicator.show is True
    
    indicator.disable()
    assert indicator.show is False
    
    indicator.enable()
    assert indicator.show is True


def test_ask_many_uses_progress_indicator(capsys):
    """Test that ask_many also uses progress indicator."""
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider, show_progress=True, auto_setup=False)
    
    prompts = ["Question 1", "Question 2"]
    responses = client.ask_many(prompts)
    
    # Should have progress output
    captured = capsys.readouterr()
    assert "Waiting for AI response" in captured.out
    assert "completed in" in captured.out


def test_ask_json_uses_progress_indicator(capsys):
    """Test that ask_json also uses progress indicator."""
    fake_provider = FakeProvider(['{"result": "success"}'])
    client = AiClient(provider=fake_provider, show_progress=True, auto_setup=False)
    
    response = client.ask_json("Return JSON")
    
    # Should have progress output
    captured = capsys.readouterr()
    assert "Waiting for AI response" in captured.out
    assert "completed in" in captured.out
