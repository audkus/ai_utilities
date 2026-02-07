#!/usr/bin/env python3
"""
Test the automated test runner to ensure stable results schema.
"""

import subprocess
import sys
from pathlib import Path


def test_examples_category_no_keyerror():
    """Test that examples category runs without KeyError."""
    project_root = Path(__file__).parent.parent
    
    # Run the automated test runner for examples category
    cmd = [sys.executable, str(project_root / "tests" / "automated_test_runner.py"), "--category", "examples"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # The main goal: no KeyError in output
    assert "KeyError" not in result.stderr, f"KeyError found in stderr: {result.stderr}"
    assert "KeyError" not in result.stdout, f"KeyError found in stdout: {result.stdout}"
    
    print("✅ Examples category test passed - no KeyError, proper schema")


def test_stable_results_schema():
    """Test that the _new_results method creates stable schema."""
    # Import the runner class
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tests.automated_test_runner import AutomatedTestRunner
    
    runner = AutomatedTestRunner()
    
    # Test different status values
    for status in ["passed", "failed", "skipped"]:
        results = runner._new_results(status=status)
        
        # Check all required keys exist
        required_keys = ["status", "tests_run", "tests_passed", "tests_failed", "errors", "duration", "details"]
        for key in required_keys:
            assert key in results, f"Missing key '{key}' in results for status '{status}'"
        
        # Check types
        assert isinstance(results["errors"], list), f"Errors should be list, got {type(results['errors'])}"
        assert isinstance(results["details"], dict), f"Details should be dict, got {type(results['details'])}"
        
        print(f"✅ Stable schema for status '{status}'")


if __name__ == "__main__":
    test_stable_results_schema()
    test_examples_category_no_keyerror()
    print("🎉 All automated test runner schema tests passed!")
