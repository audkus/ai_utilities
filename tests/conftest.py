"""Pytest configuration and fixtures."""

import logging
import os
import sys
from pathlib import Path

# Add src to path for imports ONLY if ai_utilities is not already importable
# This allows tests to work both with editable installs and local dev
try:
    import ai_utilities
    # Already importable, no need to modify sys.path
except ImportError:
    # Not importable, add src to path for local dev convenience
    src_path = str(Path(__file__).parent.parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

# Configure test logging
test_debug = os.getenv("AI_UTILITIES_TEST_DEBUG", "0") == "1"
if not test_debug:
    # Suppress logging during test collection unless debug mode is enabled
    logging.getLogger().setLevel(logging.CRITICAL)

# Load .env file for environment variables
try:
    from dotenv import load_dotenv
    # Look for .env in the project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        if test_debug:
            print(f"✅ Loaded environment from: {env_path}")
    else:
        if test_debug:
            print(f"⚠️  .env file not found at: {env_path}")
except ImportError:
    if test_debug:
        print("⚠️  dotenv not available, tests may need manual environment setup")

# Ensure critical environment variables are available
if not os.getenv("AI_API_KEY"):
    if test_debug:
        print("⚠️  AI_API_KEY not found in environment - integration tests may fail")
