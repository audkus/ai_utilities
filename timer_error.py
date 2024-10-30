import logging
import sys
import threading
import time
from typing import Optional


class _BufferingHandler(logging.Handler):
    """A custom logging handler to buffer logs and display them after the timer finishes."""

    def __init__(self):
        super().__init__()
        self.buffer = []

    def emit(self, record: logging.LogRecord) -> None:
        """Buffers the log record."""
        self.buffer.append(self.format(record))

    def display_logs(self) -> None:
        """Displays the buffered log records, ensuring they start on a new line."""
        # Print a newline first to ensure logs are separated from the timer output
        sys.stdout.write('\n')
        sys.stdout.flush()  # Flush to make sure the new line is written immediately
        for record in self.buffer:
            print(record)


def ask_ai(prompt: str) -> str:
    """Simulates sending a prompt to the AI model and returns a dummy response."""
    time.sleep(2)  # Simulate AI processing time
    return f"Response to: {prompt}"


def main() -> None:
    """Demonstrates the example usage of the module."""

    # Create the buffering handler and configure logging to use it
    buffer_handler = _BufferingHandler()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Set log level to INFO to see log messages
    logger.addHandler(buffer_handler)

    prompt = "What is the capital of France?"

    stop_timer = threading.Event()
    start_time = time.time()
    output_lock = threading.Lock()  # This lock ensures only one thread accesses the output

    # Start a single timer (this will be shown only once regardless of threads)
    timer_thread = threading.Thread(target=_timer,
                                    args=(start_time, stop_timer, output_lock))  # Corrected order of arguments
    timer_thread.start()

    try:
        # Simulate multiple threads submitting tasks
        thread_pool = []
        for i in range(3):
            thread = threading.Thread(target=_ai_worker, args=(prompt, logger, output_lock))
            thread_pool.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in thread_pool:
            thread.join()
    finally:
        stop_timer.set()
        timer_thread.join()
        buffer_handler.display_logs()
        logger.removeHandler(buffer_handler)


def _ai_worker(prompt: str, logger: logging.Logger, output_lock: threading.Lock) -> None:
    """Simulates an AI worker thread sending a prompt to the AI."""
    response = ask_ai(prompt)
    with output_lock:  # Ensure that only one thread prints to the output at a time
        logger.info(f"AI Response: {response}")


def _timer(start_time: float, stop_timer: threading.Event, output_lock: threading.Lock) -> None:
    """Displays a single timer while waiting for the AI response."""
    try:
        while not stop_timer.is_set():
            elapsed_time = int(time.time() - start_time)
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            message = f"\rWaiting for AI response [{hours:02}:{minutes:02}:{seconds:02}]"

            with output_lock:  # Ensure the timer has exclusive access to the output line
                sys.stdout.write(message)
                sys.stdout.flush()
            time.sleep(1)
    finally:
        with output_lock:
            sys.stdout.write('\n')  # Move to a new line when the timer stops
            sys.stdout.flush()


if __name__ == "__main__":
    main()
