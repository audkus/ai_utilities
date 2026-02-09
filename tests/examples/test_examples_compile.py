"""
Compile-only tests for examples/

Ensures all Python files in examples/ can be compiled without syntax errors.
"""

import pathlib
import py_compile
from typing import List

import pytest


def get_example_python_files() -> List[pathlib.Path]:
    """Get all Python files in examples/ directory, excluding outputs and cache."""
    examples_dir = pathlib.Path(__file__).parent.parent.parent / "examples"
    python_files = []
    
    for py_file in examples_dir.rglob("*.py"):
        # Skip outputs directory (generated files)
        if "outputs" in py_file.parts:
            continue
            
        # Skip __pycache__ directories
        if "__pycache__" in py_file.parts:
            continue
            
        python_files.append(py_file)
    
    return sorted(python_files)


@pytest.mark.parametrize("py_file", get_example_python_files())
def test_example_compiles(py_file: pathlib.Path) -> None:
    """Test that each example Python file compiles without syntax errors."""
    try:
        py_compile.compile(str(py_file), doraise=True)
    except py_compile.PyCompileError as e:
        pytest.fail(f"Example file {py_file.relative_to(py_file.parents[2])} failed to compile: {e}")


def test_all_examples_found() -> None:
    """Verify we found the expected number of example files."""
    python_files = get_example_python_files()
    
    # We expect at least some files (adjust if structure changes)
    assert len(python_files) >= 10, f"Expected at least 10 example files, found {len(python_files)}"
    
    # Check we have files in expected directories
    dirs_found = {py_file.parent.name for py_file in python_files if py_file.parent.name != "examples"}
    expected_dirs = {"quickstarts", "advanced", "providers"}
    
    for expected_dir in expected_dirs:
        assert any(expected_dir in str(p) for p in python_files), f"No files found in {expected_dir}/ directory"
