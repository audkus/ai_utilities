"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load .env file for environment variables
try:
    from dotenv import load_dotenv
    # Look for .env in the project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
except ImportError:
    print("⚠️  dotenv not available, tests may need manual environment setup")

# Ensure critical environment variables are available
if not os.getenv("AI_API_KEY"):
    print("⚠️  AI_API_KEY not found in environment - integration tests may fail")
