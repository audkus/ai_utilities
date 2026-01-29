"""Syntax validation tests for examples.

This test only validates that examples can be compiled (syntax check).
It does NOT execute examples or require API keys.
"""

import subprocess
import sys
from pathlib import Path


def test_examples_syntax():
    """Test that all example files have valid Python syntax."""
    examples_dir = Path(__file__).parent.parent / "examples"
    
    # Find all Python files in examples directory
    python_files = list(examples_dir.glob("*.py"))
    
    # Skip setup_examples.py as it's a special case
    python_files = [f for f in python_files if f.name != "setup_examples.py"]
    
    assert python_files, "No Python example files found"
    
    for example_file in python_files:
        # Use compileall to check syntax without execution
        result = subprocess.run(
            [sys.executable, "-m", "compileall", str(example_file)],
            capture_output=True,
            text=True,
            cwd=examples_dir.parent
        )
        
        # compileall returns 0 on success, non-zero on syntax errors
        assert result.returncode == 0, f"Syntax error in {example_file.name}: {result.stderr}"
