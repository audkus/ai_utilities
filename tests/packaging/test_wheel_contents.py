"""Test wheel contents validation."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Set

import pytest

pytestmark = pytest.mark.packaging


def test_wheel_contains_only_runtime_files() -> None:
    """
    Test that wheel contains only runtime files, no development artifacts.
    
    Wheel should be minimal - only code and metadata needed for runtime.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    forbidden_patterns = {
        "tests/",
        "docs/",
        "examples/",
        "scripts/",
        ".github/",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "build/",
        "dist/",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".DS_Store",
        "*.log",
        "*.tmp",
        "*.bak",
    }

    violations = []
    
    with zipfile.ZipFile(wheel, "r") as zf:
        for name in zf.namelist():
            # Skip directory entries
            if name.endswith("/"):
                continue
                
            # Check for forbidden patterns
            for pattern in forbidden_patterns:
                if pattern.endswith("/"):
                    # Directory pattern
                    if name.startswith(pattern):
                        violations.append(f"{name} (matches pattern {pattern})")
                        break
                else:
                    # File pattern
                    if pattern in name:
                        violations.append(f"{name} (matches pattern {pattern})")
                        break

    assert not violations, (
        f"Wheel contains forbidden files:\n"
        f"- " + "\n- ".join(sorted(violations))
    )


def test_wheel_contains_essential_files() -> None:
    """
    Test that wheel contains essential runtime files.
    
    Wheel should contain all necessary Python modules and metadata.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    # Essential files that should be in the wheel
    required_patterns = {
        "ai_utilities/__init__.py",
        "ai_utilities/client.py",
        "ai_utilities/config_models.py",
        "ai_utilities/exceptions.py",
        "ai_utilities/models.py",
        "ai_utilities-",
        ".dist-info/METADATA",
        ".dist-info/RECORD",
        ".dist-info/WHEEL",
        ".dist-info/entry_points.txt",
        ".dist-info/top_level.txt",
    }

    found_files = set()
    
    with zipfile.ZipFile(wheel, "r") as zf:
        for name in zf.namelist():
            found_files.add(name)

    missing = []
    for pattern in required_patterns:
        found = any(pattern in name for name in found_files)
        if not found:
            missing.append(pattern)

    assert not missing, (
        f"Wheel is missing essential files:\n"
        f"- " + "\n- ".join(sorted(missing))
    )


def test_wheel_no_duplicate_files() -> None:
    """
    Test that wheel doesn't contain duplicate files.
    
    Duplicates can cause installation issues.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    file_counts = {}
    duplicates = []
    
    with zipfile.ZipFile(wheel, "r") as zf:
        for name in zf.namelist():
            # Normalize path separators for comparison
            normalized = name.replace("\\", "/")
            file_counts[normalized] = file_counts.get(normalized, 0) + 1
            if file_counts[normalized] > 1:
                duplicates.append(normalized)

    assert not duplicates, (
        f"Wheel contains duplicate files:\n"
        f"- " + "\n- ".join(sorted(set(duplicates)))
    )


def test_wheel_metadata_consistency() -> None:
    """
    Test that wheel metadata is consistent and valid.
    
    Checks for proper metadata structure and required fields.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    metadata_files = []
    entry_points_file = None
    
    with zipfile.ZipFile(wheel, "r") as zf:
        for name in zf.namelist():
            if name.endswith(".dist-info/") or ".dist-info/" in name:
                metadata_files.append(name)
            elif name.endswith(".dist-info/entry_points.txt"):
                entry_points_file = name
    
    # Check we have metadata files (not necessarily directories)
    assert len(metadata_files) >= 4, f"Expected metadata files, found {len(metadata_files)}"
    
    # Check entry points file exists
    assert entry_points_file is not None, "Wheel missing entry_points.txt"
    
    # Check entry points content
    with zipfile.ZipFile(wheel, "r") as zf:
        entry_points_content = zf.read(entry_points_file).decode("utf-8")
        
        # Should contain console script for ai-utilities
        assert "console_scripts" in entry_points_content
        assert "ai-utilities" in entry_points_content
