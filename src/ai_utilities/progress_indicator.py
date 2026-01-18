"""Progress indicator for AI requests with configurable display."""

import sys
import threading
import time
from typing import Optional


class ProgressIndicator:
    """Shows a progress indicator with elapsed time during AI requests."""
    
    def __init__(self, message: str = "Waiting for AI response", show: bool = True):
        """Initialize progress indicator.
        
        Args:
            message: Message to display while waiting
            show: Whether to show the progress indicator
        """
        self.message = message
        self.show = show
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_time: Optional[float] = None
        # Don't start thread in __init__ - wait for __enter__/start()
    
    def __enter__(self):
        """Start the progress indicator."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the progress indicator."""
        self.stop()
    
    def start(self):
        """Start the progress indicator thread."""
        if not self.show:
            return
        
        if self._thread and self._thread.is_alive():
            # Already started
            return
        
        self._start_time = time.time()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._update_display, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the progress indicator."""
        if not self.show:
            return
        
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        # Show final time
        if self._start_time:
            elapsed = int(time.time() - self._start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Clear the current line and show final message
            sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
            sys.stdout.write(f"{self.message} completed in [{hours:02d}:{minutes:02d}:{seconds:02d}]\n")
            sys.stdout.flush()
    
    def _update_display(self):
        """Update the progress display in a separate thread."""
        # Store start time when thread starts to avoid repeated time.time() calls
        start_time = self._start_time
        if not start_time:
            return
        
        while not self._stop_event.is_set():
            # Calculate elapsed time based on start time - no time.time() in loop
            current_elapsed = int(time.time() - start_time)
            hours, remainder = divmod(current_elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            message = f"\r{self.message} [{hours:02d}:{minutes:02d}:{seconds:02d}]"
            sys.stdout.write(message)
            sys.stdout.flush()
            
            # Update every second
            time.sleep(1)
    
    def disable(self):
        """Disable the progress indicator."""
        self.show = False
    
    def enable(self):
        """Enable the progress indicator."""
        self.show = True
