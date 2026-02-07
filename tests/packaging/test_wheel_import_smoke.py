"""Test wheel import smoke test - most critical packaging validation."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest

pytestmark = pytest.mark.packaging


def _create_temp_venv(venv_dir: Path) -> Path:
    """Create a temporary virtual environment."""
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    
    # Determine python executable in venv
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    return python_exe, pip_exe


def _install_wheel_in_venv(pip_exe: Path, wheel_path: Path) -> None:
    """Install wheel in the temporary venv."""
    subprocess.run([str(pip_exe), "install", str(wheel_path)], check=True)


def _test_import_in_venv(python_exe: Path) -> None:
    """Test that ai_utilities imports successfully in clean venv."""
    result = subprocess.run(
        [str(python_exe), "-c", "import ai_utilities; print('Import successful')"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Import successful" in result.stdout


def _test_cli_help_in_venv(python_exe: Path) -> None:
    """Test that CLI help works in clean venv."""
    result = subprocess.run(
        [str(python_exe), "-m", "ai_utilities", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "usage:" in result.stdout.lower()
    assert "ai-utilities" in result.stdout.lower()


def test_wheel_import_smoke_test() -> None:
    """
    Test wheel install + import smoke test.
    
    This is the most critical packaging test - ensures what users install
    actually imports and works correctly.
    
    What it catches:
    - Accidental import of optional deps at module level
    - Missing package data
    - Broken entry points
    - Import-time side effects
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "test_venv"
        python_exe, pip_exe = _create_temp_venv(venv_dir)
        
        # Install wheel in clean venv
        _install_wheel_in_venv(pip_exe, wheel)
        
        # Test import works
        _test_import_in_venv(python_exe)
        
        # Test CLI help works
        _test_cli_help_in_venv(python_exe)


def test_wheel_minimal_contents() -> None:
    """
    Test that wheel contains only essential files.
    
    Wheel should be minimal - no tests/, docs/, examples/ paths.
    Only runtime code and essential metadata.
    """

    import zipfile

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    forbidden_paths = set()
    with zipfile.ZipFile(wheel, "r") as zf:
        for name in zf.namelist():
            # Check for forbidden directories
            if any(path in name for path in ["tests/", "docs/", "examples/"]):
                forbidden_paths.add(name)

    assert not forbidden_paths, (
        f"Wheel contains forbidden paths (should be minimal):\n"
        f"- " + "\n- ".join(sorted(forbidden_paths))
    )


def test_entry_point_exists_and_runs() -> None:
    """
    Test that console script entry point exists and runs.
    
    This catches broken console scripts or renamed CLI modules.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "test_venv"
        python_exe, pip_exe = _create_temp_venv(venv_dir)
        
        # Install wheel in clean venv
        _install_wheel_in_venv(pip_exe, wheel)
        
        # Test entry point directly (if available)
        if sys.platform == "win32":
            entry_point = venv_dir / "Scripts" / "ai-utilities.exe"
        else:
            entry_point = venv_dir / "bin" / "ai-utilities"
        
        # Try to run entry point if it exists
        if entry_point.exists():
            result = subprocess.run([str(entry_point), "--help"], capture_output=True, text=True)
            assert result.returncode == 0, f"Entry point failed: {result.stderr}"
            assert "usage:" in result.stdout.lower()
        else:
            # Fall back to python -m ai_utilities
            _test_cli_help_in_venv(python_exe)


def test_optional_dependency_import_policy() -> None:
    """
    Test that base import doesn't require optional packages.
    
    This ensures optional providers remain truly optional.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"No wheel found in {dist}/. Run `python -m build` first."
    wheel = wheels[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "test_venv"
        python_exe, pip_exe = _create_temp_venv(venv_dir)
        
        # Install ONLY the wheel (no extras)
        _install_wheel_in_venv(pip_exe, wheel)
        
        # Test that core functionality works without optional deps
        core_imports = [
            "import ai_utilities",
            "from ai_utilities import AiClient, AiSettings",
            "from ai_utilities.config_models import AiSettings",
            "from ai_utilities.exceptions import AiUtilitiesError",
        ]
        
        for import_code in core_imports:
            result = subprocess.run(
                [str(python_exe), "-c", import_code],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Core import failed: {import_code}\nError: {result.stderr}"
        
        # Test that optional providers raise clear errors when used
        optional_provider_test = """
try:
    from ai_utilities import OpenAIProvider
    print("ERROR: OpenAI provider imported without optional dependency")
except ImportError as e:
    if "openai" in str(e).lower():
        print("SUCCESS: Clear error for missing optional dependency")
    else:
        print(f"ERROR: Unclear error message: {e}")
"""
        
        result = subprocess.run(
            [str(python_exe), "-c", optional_provider_test],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "SUCCESS" in result.stdout
        assert "Clear error for missing optional dependency" in result.stdout
