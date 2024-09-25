
"""
rate_limiter.py

This module provides the `RateLimiter` class, which manages and enforces rate limits for API calls.
It ensures that requests and token usage are constrained according to predefined limits, such as
Requests Per Minute (RPM), Tokens Per Minute (TPM), and Tokens Per Day (TPD). The `RateLimiter`
also supports multithreaded environments, making it safe to use across concurrent requests.

Key functionalities include:
- Enforcing rate limits for requests and token usage based on predefined settings.
- Providing thread-safe access to shared resources to prevent race conditions.
- Automatically resetting daily and per-minute limits for API usage.
- Recording usage and saving statistics to a file to persist limits across sessions.
- Supporting background timers for periodic resets of the per-minute counters.

Example usage:

from rate_limiter import RateLimiter

# Initialize rate limiter with specific limits for API usage
rate_limiter = RateLimiter(module_name="gpt-4", rpm=60, tpm=1000, tpd=10000)

# Check if a request with 500 tokens can proceed
if rate_limiter.can_proceed(500):
    # Record the usage once the request is made
    rate_limiter.record_usage(500)
    print("Request can proceed")
else:
    print("Rate limit exceeded")

# Start the background thread to reset the per-minute counters
rate_limiter.start_reset_timer()
"""
# Standard Library Imports
import threading
import json
import os
import time
import datetime
from datetime import datetime
from typing import Optional


class RateLimiter:
    """
    A class to manage and limit the rate of API calls, specifically tracking and enforcing
    limits on Requests Per Minute (RPM), Tokens Per Minute (TPM), and Tokens Per Day (TPD).

    The class ensures thread-safe access to shared resources using locks to prevent race conditions
    when multiple threads attempt to check or update the rate limits concurrently.

    Attributes:
        module_name (str): The name of the AI model being used (e.g., 'gpt-4').
        rpm (int): The maximum number of requests allowed per minute.
        tpm (int): The maximum number of tokens allowed per minute.
        tpd (int): The maximum number of tokens allowed per day.
        ai_stats_file (str): Path to the file where usage statistics are stored.
        requests_made (int): Counter for the number of requests made in the current minute.
        tokens_used (int): Counter for the number of tokens used in the current minute.
        tokens_used_today (int): Counter for the number of tokens used today.
        last_reset (datetime): The last time the daily usage was reset.
        lock (threading.Lock): A lock to ensure thread-safe access to shared resources.
    """

    def __init__(self, module_name: str, rpm: int, tpm: int, tpd: int,
                 config_path: str, ask_ai_statistics_file_name: str = "ai_statistics.json") -> None:
        """
        Initializes the RateLimiter with specified limits and loads the current usage statistics
        from the provided stats file. The class ensures that rate limits on requests and tokens
        are enforced.

        Args:
            module_name (str): The name of the AI model being used (e.g., 'gpt-4').
            rpm (int): The maximum number of requests allowed per minute.
            tpm (int): The maximum number of tokens allowed per minute.
            tpd (int): The maximum number of tokens allowed per day.
            ask_ai_statistics_file_name (str, optional): Path to the file where usage statistics are stored.
                                           Defaults to "ai_statistics.json".
        """
        self.module_name = module_name
        self.rpm = rpm
        self.tpm = tpm
        self.tpd = tpd

        # Derive the path for the stats file based on the config directory
        config_dir = os.path.dirname(config_path)
        self.ai_stats_file = os.path.join(config_dir, ask_ai_statistics_file_name)

        self.requests_made = 0
        self.tokens_used = 0
        self.tokens_used_today = 0
        self.last_reset = datetime.now().isoformat()

        # Lock for synchronizing access to shared resources
        self.lock = threading.Lock()

        # Load or initialize stats
        self.load_stats()

    def load_stats(self) -> None:
        """
        Loads the current usage statistics from the stats file. If the file does not exist,
        it initializes the statistics with default values.
        """
        if os.path.exists(self.ai_stats_file):
            with open(self.ai_stats_file, "r") as file:
                data = json.load(file)
                self.tokens_used_today = data.get("tokens_used_today", 0)
                self.last_reset = datetime.fromisoformat(data.get("last_reset", datetime.now().isoformat()))
                # Ensure the stats file includes the current module and its limits
                data.setdefault("module_name", self.module_name)
                data.setdefault("max_limits", {"tpd": self.tpd})
                self.save_stats(data)
        else:
            self.reset_daily_usage()

    def save_stats(self, data: Optional[dict] = None) -> None:
        """
        Saves the current usage statistics to the stats file.

        Args:
            data (Optional[dict]): The data to be saved to the stats file. If None, current stats will be saved.
        """
        if data is None:
            data = {
                "tokens_used_today": self.tokens_used_today,
                "last_reset": self.last_reset.isoformat(),
                "module_name": self.module_name,
                "max_limits": {"tpd": self.tpd}
            }
        with open(self.ai_stats_file, "w") as file:
            json.dump(data, file)

    def reset_daily_usage(self) -> None:
        """
        Resets the daily usage statistics, setting the token usage for today to zero and
        updating the last reset timestamp.
        """
        self.tokens_used_today = 0
        self.last_reset = datetime.now()
        self.save_stats()

    def can_proceed(self, tokens: int) -> bool:
        """
        Checks if the current request can proceed without exceeding the defined rate limits.

        This method ensures thread-safety by using a lock to prevent race conditions when checking
        the number of requests and tokens used.

        Args:
            tokens (int): The number of tokens that the current request will consume.

        Returns:
            bool: True if the request can proceed without exceeding the rate limits, False otherwise.
        """
        with self.lock:
            self.check_reset()
            can_proceed = (self.requests_made < self.rpm) and (self.tokens_used + tokens <= self.tpm) and (
                    self.tokens_used_today + tokens <= self.tpd)
            return can_proceed

    def record_usage(self, tokens: int) -> None:
        """
        Records the usage of a request, updating the request and token counters. It ensures thread-safety
        by using a lock to prevent race conditions.

        Args:
            tokens (int): The number of tokens used by the current request.
        """
        with self.lock:
            self.requests_made += 1
            self.tokens_used += tokens
            self.tokens_used_today += tokens
            self.save_stats()

    def check_reset(self) -> None:
        """
        Checks if a daily reset is needed (i.e., if a new day has started since the last reset)
        and performs the reset if necessary. This ensures the usage counters are reset at the start
        of a new day.

        This method is thread-safe.
        """
        if datetime.now().date() > self.last_reset.date():
            self.reset_daily_usage()

    def reset_minute_counters(self) -> None:
        """
        Resets the request and token counters for the current minute. This method is thread-safe
        and ensures that counters are reset appropriately without race conditions.
        """
        with self.lock:
            self.requests_made = 0
            self.tokens_used = 0

    def start_reset_timer(self) -> None:
        """
        Starts a background thread that resets the request and token counters every minute. This
        method is intended to ensure that rate limits are reset at regular intervals.

        The background thread runs in daemon mode and will terminate when the main thread exits.
        """

        def reset():
            while True:
                time.sleep(60)  # Reset every minute
                self.reset_minute_counters()

        thread = threading.Thread(target=reset)
        thread.daemon = True
        thread.start()

def main():
    # Initialize rate limiter with specific limits for API usage
    rate_limiter = RateLimiter(module_name="gpt-4", rpm=60, tpm=1000, tpd=10000, config_path="./config.ini")

    # Start the background thread to reset the per-minute counters
    rate_limiter.start_reset_timer()

    # Simulate API calls
    for _ in range(10):  # Example: making 10 requests
        tokens = 500  # Each request uses 500 tokens
        if rate_limiter.can_proceed(tokens):
            rate_limiter.record_usage(tokens)
            print(f"Request with {tokens} tokens can proceed.")
        else:
            print(f"Rate limit exceeded for {tokens} tokens.")

        time.sleep(5)  # Simulate a wait time between requests

if __name__ == "__main__":
    main()