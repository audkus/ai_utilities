#!/usr/bin/env python3
"""Run packaging smoke tests manually."""

import os
import sys
import tempfile
from pathlib import Path

# Add tests to path
tests_path = Path(__file__).parent / "tests"
sys.path.insert(0, str(tests_path))

# Set environment variable
os.environ['RUN_PACKAGING_TESTS'] = '1'

# Import the test module
from packaging.test_pip_install_import import (
    test_wheel_install_no_deps_import_smoke,
    test_wheel_install_with_deps_cli_help_and_import,
    test_wheel_install_openai_extra_cli_help_and_openai_provider_import,
)

def main():
    """Run all packaging tests."""
    print("Running packaging smoke tests...")
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        
        try:
            print("Running test_wheel_install_no_deps_import_smoke...")
            test_wheel_install_no_deps_import_smoke(tmp_path)
            print("✓ PASSED")
            
            print("Running test_wheel_install_with_deps_cli_help_and_import...")
            test_wheel_install_with_deps_cli_help_and_import(tmp_path)
            print("✓ PASSED")
            
            print("Running test_wheel_install_openai_extra_cli_help_and_openai_provider_import...")
            test_wheel_install_openai_extra_cli_help_and_openai_provider_import(tmp_path)
            print("✓ PASSED")
            
            print("\nAll packaging tests passed! ✓")
            return 0
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
