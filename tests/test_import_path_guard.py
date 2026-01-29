"""Import Path Guard - Prevents coverage measurement regression.

This test ensures that ai_utilities is imported from the repository source
rather than an installed package, which would cause misleading coverage
results like "module was never imported".

The guard detects the common coverage regression scenario where:
1. An installed ai_utilities package shadows the repo source
2. Tests import from site-packages instead of src/
3. Coverage measurement becomes incorrect due to import-path ambiguity

This test is deterministic, requires no network/API keys, and executes quickly.
"""

import pathlib
import sys


def test_ai_utilities_imported_from_repo_source():
    """Guard test: Ensure ai_utilities is imported from repo src/, not site-packages.
    
    This test prevents coverage measurement regression by enforcing that
    ai_utilities is imported from the repository source directory.
    
    Failure indicates:
    - An installed package is shadowing the repo source
    - Coverage measurement would be misleading
    - Need to uninstall global package or fix import paths
    
    Fix: Use canonical coverage command:
        python -m coverage run -m pytest
    """
    # Import ai_utilities (this should use src/ due to pytest.ini pythonpath=src)
    import ai_utilities
    
    # Get the actual file location and resolve to absolute path
    actual_file = pathlib.Path(ai_utilities.__file__).resolve()
    
    # Determine repository root (this test file's parent's parent)
    repo_root = pathlib.Path(__file__).parent.parent.resolve()
    expected_src_dir = repo_root / "src" / "ai_utilities"
    
    # The actual file should be under the expected src directory
    expected_file = expected_src_dir / "__init__.py"
    
    # Assert that we're importing from the repo source, not site-packages
    assert actual_file == expected_file, (
        f"IMPORT PATH GUARD FAILED: ai_utilities imported from wrong location\n"
        f"  Expected: {expected_file}\n"
        f"  Actual:   {actual_file}\n"
        f"\n"
        f"This causes misleading coverage results (e.g., 'module was never imported').\n"
        f"\n"
        f"COMMON CAUSES:\n"
        f"  1. Installed ai_utilities package shadows repo source\n"
        f"  2. Python path configuration issue\n"
        f"  3. Virtual environment not activated\n"
        f"\n"
        f"FIXES:\n"
        f"  1. Uninstall global package: pip uninstall ai-utilities\n"
        f"  2. Use canonical coverage command: python -m coverage run -m pytest\n"
        f"  3. Ensure pytest.ini has 'pythonpath = src'\n"
        f"  4. Activate virtual environment with dev dependencies\n"
        f"\n"
        f"COVERAGE CORRECTNESS:\n"
        f"  The canonical command 'python -m coverage run -m pytest' ensures\n"
        f"  coverage starts BEFORE imports, preventing measurement issues."
    )
    
    # Additional verification: ensure we're not in site-packages
    site_packages_paths = [path for path in sys.path if "site-packages" in path]
    for site_path in site_packages_paths:
        assert not actual_file.is_relative_to(pathlib.Path(site_path)), (
            f"IMPORT PATH GUARD FAILED: ai_utilities imported from site-packages\n"
            f"  File location: {actual_file}\n"
            f"  Site-packages path: {site_path}\n"
            f"\n"
            f"This breaks coverage measurement. See above for fixes."
        )
