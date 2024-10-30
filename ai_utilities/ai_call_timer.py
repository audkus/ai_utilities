"""
ai_call_timer.py

This module provides a context manager for displaying a timer while waiting for AI responses.
It also sets up a buffering log handler to capture and display logs after the timer completes.

Key functionalities include:
- Displaying a non-blocking timer while waiting for AI responses.
- Buffering log messages and displaying them after the timer stops.

Example usage:
    from ai_call_timer import AICallTimer

    with AICallTimer():
        # Perform some AI-related tasks here
        pass

Executing main in module for test use:
    python -m ai_utilities.ai_call_timer
"""

# Standard Library Imports
import threading
import time
import sys
import logging
from typing import Optional

# Local application Imports
from .buffer_handler import BufferedLogHandler

logger = logging.getLogger(__name__)
_timer_started = False


class AICallTimer:
    """
    A context manager that displays a timer while interacting with AI models
    and buffers log messages during the operation.

    Attributes:
        log_level (int): The logging level for the buffer handler.
        stop_timer (threading.Event): Event to signal when to stop the timer.
        start_time (Optional[float]): The time when the timer started.
        output_lock (threading.Lock): A lock to control console output.
        buffer_handler (BufferedLogHandler): A handler to buffer log messages.
    """

    def __init__(self, log_level: Optional[int] = None) -> None:
        """
        Initializes the AICallTimer with the specified logging level.

        Args:
            log_level (int): The logging level to use for the buffer handler. Defaults to logging.INFO.
        """
        self.stop_timer: threading.Event = threading.Event()
        self.start_time: Optional[float] = None
        self.output_lock: threading.Lock = threading.Lock()
        self.log_level: int = log_level
        self.buffer_handler: Optional[BufferedLogHandler] = None

    def __enter__(self) -> BufferedLogHandler:
        """
        Sets up the buffering log handler and starts the timer.

        Returns:
            BufferedLogHandler: The handler to buffer log messages.
        """
        global _timer_started

        # Configure the logger and add the buffer handler
        logging.basicConfig(level=self.log_level, format="%(asctime)s - %(levelname)s - %(message)s")
        self.buffer_handler = BufferedLogHandler()
        logger.addHandler(self.buffer_handler)

        # Start the timer only if it's not already running
        self.start_time = time.time()
        if not _timer_started:
            _timer_started = True
            timer_thread = threading.Thread(target=self._timer)
            timer_thread.start()

        return self.buffer_handler

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Stops the timer and flushes any buffered log messages.

        Args:
            exc_type (Optional[Type[BaseException]]): The exception type, if any.
            exc_val (Optional[BaseException]]): The exception value, if any.
            exc_tb (Optional[Traceback]]): The traceback, if any.

        Returns:
            bool: False to propagate any exceptions.
        """
        global _timer_started
        self.stop_timer.set()  # Stop the timer immediately after the response
        _timer_started = False

        if self.buffer_handler:
            self._display_final_time()
            self.buffer_handler.display_logs()
            logger.removeHandler(self.buffer_handler)

    def _timer(self) -> None:
        """
        Continuously updates the console with the elapsed time in the format [HH:MM:SS]
        while waiting for an AI response.

        The timer runs until `stop_timer` is set, at which point it displays the final time.
        """
        while not self.stop_timer.is_set():
            self._display_elapsed_time()
            time.sleep(1)

    def _display_elapsed_time(self) -> None:
        """
        Calculates and displays the elapsed time in the format [HH:MM:SS].

        This method acquires a lock on the output to ensure consistent console updates.
        """
        elapsed_time: int = int(time.time() - self.start_time)  # Calculate elapsed time in seconds
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        with self.output_lock:  # Ensure output is not interrupted
            sys.stdout.write(f"\rWaiting for AI response [{hours:02}:{minutes:02}:{seconds:02}]")
            sys.stdout.flush()

    def _display_final_time(self) -> None:
        """Displays the final elapsed time once when the timer stops."""
        elapsed_time = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        with self.output_lock:
            sys.stdout.write(f"\rWaiting for AI response [{hours:02}:{minutes:02}:{seconds:02}]\n")
            sys.stdout.flush()


def main() -> None:
    """
    Main function to demonstrate how the AICallTimer can be used.
    """
    logging.basicConfig(level=logging.DEBUG)

    # Example usage of AICallTimer
    with AICallTimer(log_level=logging.DEBUG):
        time.sleep(5)  # Simulate an AI call with a 5-second delay


if __name__ == "__main__":
    main()
