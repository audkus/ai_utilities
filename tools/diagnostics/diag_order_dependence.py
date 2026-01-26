#!/usr/bin/env python3
"""
Test to demonstrate order dependence of environment variable pollution.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_utilities.client import AiSettings
from ai_utilities.env_overrides import override_env


def test_first_sets_environment():
    """First test that sets AI_MODEL environment variable."""
    # Set environment variable
    os.environ["AI_MODEL"] = "test-model-from-first-test"

    # Create settings - should pick up the environment variable
    settings = AiSettings()
    print(f"First test model: {settings.model}")
    assert settings.model == "test-model-from-first-test"  # noqa: S101 - Test validation

    # Don't clean up to simulate pollution


def test_second_expects_clean_environment():
    """Second test that expects clean environment but gets polluted."""
    # This test expects the default model but will get the polluted one
    settings = AiSettings()
    print(f"Second test model: {settings.model}")

    # This will fail because the environment is polluted from the first test
    # Expected: 'gpt-3.5-turbo' (default)
    # Actual: 'test-model-from-first-test' (polluted from first test)
    assert settings.model == "gpt-3.5-turbo", (  # noqa: S101 - Test validation
        f"Expected 'gpt-3.5-turbo' but got '{settings.model}'"
    )


def test_with_override_env():
    """Test that uses override_env context manager."""
    # This should work correctly regardless of environment pollution
    with override_env({"AI_MODEL": "override-model"}):
        settings = AiSettings()
        print(f"Override test model: {settings.model}")
        assert settings.model == "override-model"  # noqa: S101 - Test validation


if __name__ == "__main__":
    # Run in order to demonstrate the issue
    print("=== Demonstrating Order Dependence ===")

    try:
        test_first_sets_environment()
        print("✓ First test passed")
    except Exception as e:
        print(f"✗ First test failed: {e}")

    try:
        test_second_expects_clean_environment()
        print("✓ Second test passed")
    except Exception as e:
        print(f"✗ Second test failed: {e}")

    try:
        test_with_override_env()
        print("✓ Override test passed")
    except Exception as e:
        print(f"✗ Override test failed: {e}")

    # Clean up
    if "AI_MODEL" in os.environ:
        del os.environ["AI_MODEL"]
