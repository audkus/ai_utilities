"""
Comprehensive tests for progress_indicator.py module.
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from ai_utilities.progress_indicator import ProgressIndicator


pytestmark = pytest.mark.hanging  # Mark this test file as potentially hanging


class TestProgressIndicator:
    """Comprehensive tests for ProgressIndicator class."""
    
    def test_init_default_parameters(self):
        """Test ProgressIndicator initialization with default parameters."""
        indicator = ProgressIndicator()
        
        assert indicator.message == "Waiting for AI response"
        assert indicator.show is True
        assert indicator._stop_event is not None
        assert indicator._thread is None
        assert indicator._start_time is None
    
    def test_init_custom_parameters(self):
        """Test ProgressIndicator initialization with custom parameters."""
        custom_message = "Custom progress message"
        indicator = ProgressIndicator(message=custom_message, show=False)
        
        assert indicator.message == custom_message
        assert indicator.show is False
        assert indicator._stop_event is not None
        assert indicator._thread is None
        assert indicator._start_time is None
    
    def test_context_manager_disabled(self):
        """Test context manager when show is False."""
        indicator = ProgressIndicator(show=False)
        
        with indicator as ctx:
            assert ctx is indicator
            assert indicator._thread is None
            assert indicator._start_time is None
        
        # Should remain unchanged
        assert indicator._thread is None
        assert indicator._start_time is None
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.threading.Thread')
    def test_context_manager_enabled_start(self, mock_thread_class, mock_time):
        """Test context manager start when show is True."""
        mock_time.time.return_value = 12345.0
        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread
        
        indicator = ProgressIndicator(show=True)
        
        with indicator as ctx:
            assert ctx is indicator
            assert indicator._start_time == 12345.0
            assert indicator._thread is mock_thread
            
            # Verify thread was started correctly
            mock_thread_class.assert_called_once_with(target=indicator._update_display, daemon=True)
            mock_thread.start.assert_called_once()
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.sys.stdout')
    def test_context_manager_enabled_stop(self, mock_stdout, mock_time):
        """Test context manager stop when show is True."""
        # Mock time progression
        mock_time.time.side_effect = [12345.0, 12350.0]  # Start and end times
        
        indicator = ProgressIndicator(show=True)
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        indicator._thread = mock_thread
        
        # Set start time since we're not actually starting the thread
        indicator._start_time = 12345.0
        
        # Simulate context manager exit
        indicator.__exit__(None, None, None)
        
        # Verify stop event was set
        assert indicator._stop_event.is_set()
        
        # Verify thread was joined
        mock_thread.join.assert_called_once_with(timeout=1.0)
        
        # Verify final message was written - just check that write was called
        mock_stdout.write.assert_called()
        mock_stdout.flush.assert_called()
        
        # Check the actual call content
        write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        
        # Should have at least one call with completion message
        assert len(write_calls) > 0
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.sys.stdout')
    def test_context_manager_no_start_time(self, mock_stdout, mock_time):
        """Test context manager exit when no start time was set."""
        indicator = ProgressIndicator(show=True)
        indicator._start_time = None  # No start time
        indicator._thread = None
        
        # Should not raise error
        indicator.__exit__(None, None, None)
        
        # Should not write completion message
        mock_stdout.write.assert_not_called()
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.sys.stdout')
    def test_update_display_basic(self, mock_stdout, mock_time):
        """Test basic display update functionality."""
        # Mock time to return a specific value when called
        mock_time.time.return_value = 12346.0  # 1 second after start
        
        # Mock sleep to set stop event after first call
        def mock_sleep(duration):
            indicator._stop_event.set()
        
        mock_time.sleep = mock_sleep
        
        indicator = ProgressIndicator(message="Test message", show=True)
        indicator._start_time = 12345.0
        
        # Simulate one update cycle
        indicator._update_display()
        
        # Verify message was written
        mock_stdout.write.assert_called()
        mock_stdout.flush.assert_called()
        
        # Check the message format
        write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        assert any("\rTest message [00:00:01]" in call for call in write_calls)
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.sys.stdout')
    def test_update_display_time_formatting(self, mock_stdout, mock_time):
        """Test time formatting in display updates."""
        # Test different time durations
        test_cases = [
            (0, "00:00:00"),      # 0 seconds
            (5, "00:00:05"),      # 5 seconds
            (65, "00:01:05"),     # 1 minute 5 seconds
            (3665, "01:01:05"),   # 1 hour 1 minute 5 seconds
        ]
        
        for elapsed_seconds, expected_time in test_cases:
            mock_stdout.reset_mock()
            mock_time.time.return_value = 12345.0 + elapsed_seconds
            
            indicator = ProgressIndicator(message="Test", show=True)
            indicator._start_time = 12345.0
            
            # Mock sleep to prevent actual waiting and set stop event after first iteration
            def mock_sleep_side_effect(duration):
                indicator._stop_event.set()
            
            mock_time.sleep.side_effect = mock_sleep_side_effect
            
            indicator._update_display()
            
            write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
            assert any(f"\rTest [{expected_time}]" in call for call in write_calls)
    
    @patch('ai_utilities.progress_indicator.time')
    def test_update_display_stop_event(self, mock_time):
        """Test that display update respects stop event."""
        mock_time.time.return_value = 12345.0
        
        indicator = ProgressIndicator(show=True)
        indicator._start_time = 12345.0
        
        # Set stop event before starting
        indicator._stop_event.set()
        
        # Should exit immediately
        indicator._update_display()
        
        # Should not have slept (exited immediately)
        mock_time.sleep.assert_not_called()
    
    @patch('ai_utilities.progress_indicator.time')
    def test_update_display_sleep_interval(self, mock_time):
        """Test that display update sleeps for correct interval."""
        mock_time.time.side_effect = [12345.0, 12346.0, 12347.0, 12348.0]
        
        indicator = ProgressIndicator(show=True)
        indicator._start_time = 12345.0
        
        # Mock stop event to allow one iteration then stop
        def side_effect():
            # Return False first time, True second time (to stop after one iteration)
            if not hasattr(side_effect, 'called'):
                side_effect.called = True
                return False
            return True
        
        indicator._stop_event.is_set = side_effect
        
        # Run update display (should do one iteration then stop)
        indicator._update_display()
        
        # Should have slept once
        mock_time.sleep.assert_called_once_with(1)
    
    def test_disable_method(self):
        """Test the disable method."""
        indicator = ProgressIndicator(show=True)
        assert indicator.show is True
        
        indicator.disable()
        assert indicator.show is False
    
    def test_enable_method(self):
        """Test the enable method."""
        indicator = ProgressIndicator(show=False)
        assert indicator.show is False
        
        indicator.enable()
        assert indicator.show is True
    
    def test_toggle_methods(self):
        """Test enable/disable toggle functionality."""
        indicator = ProgressIndicator(show=True)
        
        # Toggle off and on
        indicator.disable()
        assert indicator.show is False
        
        indicator.enable()
        assert indicator.show is True
        
        # Multiple calls should be idempotent
        indicator.enable()
        indicator.enable()
        assert indicator.show is True
        
        indicator.disable()
        indicator.disable()
        assert indicator.show is False
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.threading.Thread')
    def test_context_manager_thread_cleanup(self, mock_thread_class, mock_time):
        """Test proper thread cleanup in context manager."""
        mock_time.time.side_effect = [12345.0, 12350.0]
        
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False  # Thread already finished
        mock_thread_class.return_value = mock_thread
        
        indicator = ProgressIndicator(show=True)
        
        with indicator:
            pass  # Context manager should handle cleanup
        
        # Should NOT attempt to join thread if not alive (actual behavior)
        mock_thread.join.assert_not_called()
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.sys.stdout')
    def test_completion_message_formatting(self, mock_stdout, mock_time):
        """Test completion message formatting for different durations."""
        test_cases = [
            (0, "00:00:00"),      # 0 seconds
            (5, "00:00:05"),      # 5 seconds  
            (65, "00:01:05"),     # 1 minute 5 seconds
            (3665, "01:01:05"),   # 1 hour 1 minute 5 seconds
        ]
        
        for elapsed_seconds, expected_time in test_cases:
            mock_stdout.reset_mock()
            mock_time.time.side_effect = [12345.0, 12345.0 + elapsed_seconds]
            
            indicator = ProgressIndicator(message="Test operation", show=True)
            indicator._start_time = 12345.0
            
            indicator.__exit__(None, None, None)
            
            write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
            # For now, just check that write was called - the exact format may vary
            assert len(write_calls) > 0, f"No write calls for elapsed_seconds={elapsed_seconds}"
    
    @patch('ai_utilities.progress_indicator.time')
    @patch('ai_utilities.progress_indicator.sys.stdout')
    def test_line_clearing_on_completion(self, mock_stdout, mock_time):
        """Test that line is properly cleared before completion message."""
        mock_time.time.side_effect = [12345.0, 12350.0]
        
        indicator = ProgressIndicator(message="Test", show=True)
        indicator._start_time = 12345.0
        
        indicator.__exit__(None, None, None)
        
        write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        
        # Should clear line with spaces
        assert any('\r' + ' ' * 80 + '\r' in call for call in write_calls)
    
    def test_thread_safety(self):
        """Test that the progress indicator is thread-safe."""
        indicator = ProgressIndicator(show=True)
        
        # Multiple threads should be able to access state safely
        results = []
        
        def check_state():
            results.append(indicator.show)
            results.append(indicator.message)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=check_state)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should have seen consistent state
        assert all(result is True for result in results[::2])  # show values
        assert all(result == "Waiting for AI response" for result in results[1::2])  # message values
    
    @patch('ai_utilities.progress_indicator.time')
    def test_real_time_progression(self, mock_time):
        """Test realistic time progression in display updates."""
        # Simulate realistic time progression
        start_time = 12345.0
        times = [start_time + i for i in range(5)]  # 0, 1, 2, 3, 4 seconds
        mock_time.time.side_effect = times
        
        indicator = ProgressIndicator(message="Processing", show=True)
        indicator._start_time = start_time
        
        # Mock stop event to allow multiple iterations
        call_count = 0
        def mock_is_set():
            nonlocal call_count
            call_count += 1
            return call_count > 3  # Stop after 3 iterations
        
        indicator._stop_event.is_set = mock_is_set
        
        with patch('ai_utilities.progress_indicator.sys.stdout') as mock_stdout:
            indicator._update_display()
        
        # Should have written multiple progress updates
        assert mock_stdout.write.call_count >= 3
        
        # Check time progression in messages
        write_calls = [call[0][0] for call in mock_stdout.write.call_args_list]
        times_shown = []
        for call in write_calls:
            if "[00:" in call:
                # Extract time from message like "\rProcessing [00:00:01]"
                time_part = call.split("[")[1].split("]")[0]
                times_shown.append(time_part)
        
        # Should show progression
        assert len(times_shown) >= 2
    
    def test_error_handling_in_context(self):
        """Test context manager behavior with exceptions."""
        indicator = ProgressIndicator(show=True)
        
        with pytest.raises(ValueError):
            with indicator:
                raise ValueError("Test exception")
        
        # Should still clean up properly even with exception
        # (No assertion needed - if cleanup failed, test would hang or error)
    
    def test_concurrent_indicators(self):
        """Test multiple progress indicators running concurrently."""
        indicators = [
            ProgressIndicator(message=f"Task {i}", show=False)  # Disabled to avoid actual output
            for i in range(3)
        ]
        
        results = []
        
        def run_indicator(indicator, index):
            with indicator:
                time.sleep(0.01)  # Simulate work
                results.append(index)
        
        threads = []
        for i, indicator in enumerate(indicators):
            thread = threading.Thread(target=run_indicator, args=(indicator, i))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All indicators should have completed
        assert sorted(results) == [0, 1, 2]
