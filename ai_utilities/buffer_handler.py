"""
buffer_handler.py

This module provides a custom logging handler to buffer log messages and display them after a timer finishes.
It includes methods for emitting and displaying log records in a controlled manner.

Classes:
    BufferedLogHandler: A logging handler that buffers log records until they are ready to be displayed.

Example usage:
    from buffer_handler import BufferedLogHandler
    logger = logging.getLogger(__name__)
    buffer_handler = BufferedLogHandler()
    logger.addHandler(buffer_handler)
"""

# Standard Library Imports
import logging
import sys
from typing import List

# Local application Imports
from .exceptions import LoggingError


class BufferedLogHandler(logging.Handler):
    """
    A logging handler to buffer log messages and display them after the timer finishes.

    This handler buffers logs instead of printing them immediately, ensuring that they
    are displayed in a controlled manner after a task (such as an AI call) completes.

    Attributes:
        _buffer (List[str]): A list to store buffered log messages.

    Example:
        logger = logging.getLogger(__name__)
        buffer_handler = BufferedLogHandler()
        logger.addHandler(buffer_handler)
    """

    def __init__(self) -> None:
        """
        Initializes the BufferedLogHandler instance with an empty buffer.

        Raises:
            LoggingError: If an issue occurs during handler initialization.
        """
        super().__init__()
        self._buffer: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """
        Buffers the log record without immediately outputting it.

        Args:
            record (logging.LogRecord): The log record to be buffered.

        Raises:
            LoggingError: If there's an issue while formatting or buffering the log.
        """
        try:
            formatted_record = self.format(record)
            self._buffer.append(formatted_record)
        except Exception as e:
            logging.error(f"Failed to buffer log record: {str(e)}")
            raise LoggingError("An error occurred while buffering the log record.") from e

    def display_logs(self) -> None:
        """
        Displays the buffered log records, ensuring they start on a new line.

        Flushes the buffer and outputs each log record through logger handling.
        The buffer is cleared after displaying.

        Raises:
            LoggingError: If an issue occurs while printing the logs.
        """
        try:
            if self._buffer:
                sys.stdout.write('\n')
                sys.stdout.flush()  # Ensures the newline is written immediately
                for record in self._buffer:
                    self.handle(record)
                self._clear_buffer()
        except Exception as e:
            logging.error(f"Failed to display buffered logs: {str(e)}")
            raise LoggingError("An error occurred while displaying the buffered logs.") from e

    def _clear_buffer(self) -> None:
        """Clears the buffer after logs are displayed."""
        self._buffer = []


def main() -> None:
    """Demonstrates how to use the BufferedLogHandler."""
    logger = logging.getLogger(__name__)
    buffer_handler = BufferedLogHandler()
    logger.addHandler(buffer_handler)

    logger.setLevel(logging.INFO)
    logger.info("This is an informational message.")

    # Simulating log buffering
    buffer_handler.display_logs()  # Logs will be displayed after this call


if __name__ == "__main__":
    main()
