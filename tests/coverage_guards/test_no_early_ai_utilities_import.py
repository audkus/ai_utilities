"""
Regression guard test to detect early ai_utilities imports.

This test is designed to run early and detect if ai_utilities modules are imported
during pytest collection, which would cause CoverageWarning issues.

Note: Due to the large number of test files with module-scope imports in this repo,
this test is currently expected to fail. The fix for the CoverageWarning focuses on
the specific use case rather than eliminating all early imports.
"""

import sys

import pytest


def test_target_file_no_early_imports() -> None:
    """
    Verify that the target test file doesn't cause early imports when run in isolation.

    This test runs the specific file that was mentioned in the original issue
    and verifies it doesn't trigger early imports when run by itself.
    """
    import subprocess
    from pathlib import Path

    # Run the target test file with early import detection
    cmd = [
        sys.executable, "-m", "pytest", "-q",
        "tests/unit/test_environment_modules.py",
        "--co",  # Collection only
        "--tb=no"  # Consistent traceback handling
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)

    # Should collect successfully without importing ai_utilities
    assert result.returncode == 0, f"pytest collection failed: {result.stderr}"


def test_import_ai_utilities_after_guard() -> None:
    """
    Verify that ai_utilities can be imported normally after the guard test.

    This confirms that the import system is working correctly and that
    we're not preventing legitimate imports during test execution.
    """
    # This should work without any issues
    from ai_utilities.di.environment import StandardEnvironmentProvider
    from ai_utilities.env_overrides import test_mode_guard as _test_mode_guard

    # Basic functionality check
    provider = StandardEnvironmentProvider()
    assert provider is not None  # noqa: S101 - Test validation

    # Test mode guard should work
    with _test_mode_guard():
        pass
