"""Packaging smoke tests for ai_utilities wheel installation and import."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import pytest

pytestmark = pytest.mark.packaging

if os.environ.get("RUN_PACKAGING_TESTS") != "1":
    pytest.skip("RUN_PACKAGING_TESTS=1 required", allow_module_level=True)


@dataclass(frozen=True)
class CommandResult:
    """Result of running a command."""

    returncode: int
    stdout: str
    stderr: str


class PackagingTestError(Exception):
    """Custom exception for packaging test failures with detailed output."""

    def __init__(self, message: str, result: CommandResult) -> None:
        super().__init__(
            f"{message}\n"
            f"Return code: {result.returncode}\n"
            f"Stdout:\n{result.stdout}\n"
            f"Stderr:\n{result.stderr}"
        )
        self.result: CommandResult = result


def _run(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    """Run a command and return the result."""
    merged_env: dict[str, str] = dict(os.environ)
    if env:
        merged_env.update(dict(env))

    proc = subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def _venv_env(script_dir: Path) -> dict[str, str]:
    """Environment vars for running inside a venv (ensures venv scripts are found first)."""
    env: dict[str, str] = {
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_PYTHON_VERSION_WARNING": "1",
    }
    old_path = os.environ.get("PATH", "")
    env["PATH"] = f"{script_dir}{os.pathsep}{old_path}"
    return env


def _create_venv(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Create a virtual environment and return (venv_dir, python_bin, pip_bin, script_dir)."""
    venv_dir = tmp_path / "test_venv"

    result = _run([sys.executable, "-m", "venv", str(venv_dir)])
    if result.returncode != 0:
        raise PackagingTestError("Failed to create virtual environment", result)

    if sys.platform.startswith("win"):
        python_bin = venv_dir / "Scripts" / "python.exe"
        pip_bin = venv_dir / "Scripts" / "pip.exe"
        script_dir = venv_dir / "Scripts"
    else:
        python_bin = venv_dir / "bin" / "python"
        pip_bin = venv_dir / "bin" / "pip"
        script_dir = venv_dir / "bin"

    return venv_dir, python_bin, pip_bin, script_dir


def _build_wheel(repo_root: Path, dist_dir: Path) -> Path:
    """Build a wheel and return the wheel path."""
    dist_dir.mkdir(parents=True, exist_ok=True)

    result = _run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
        cwd=repo_root,
        env={
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_PYTHON_VERSION_WARNING": "1",
        },
    )
    if result.returncode != 0:
        raise PackagingTestError("Failed to build wheel", result)

    wheels = sorted(dist_dir.glob("*.whl"))
    if not wheels:
        raise PackagingTestError(
            "No wheel found after build", CommandResult(1, "", f"No wheel file found in {dist_dir}")
        )

    return wheels[-1]


def _run_console_script(script_dir: Path, python_bin: Path, name: str, *args: str) -> CommandResult:
    """Run a console script inside the venv with fallbacks."""
    env = _venv_env(script_dir)

    if sys.platform.startswith("win"):
        exe_path = script_dir / f"{name}.exe"
        cmd_path = script_dir / f"{name}.cmd"
        script_py = script_dir / f"{name}-script.py"

        if exe_path.exists():
            return _run([str(exe_path), *args], env=env)
        if cmd_path.exists():
            return _run([str(cmd_path), *args], env=env)
        if script_py.exists():
            return _run([str(python_bin), str(script_py), *args], env=env)

        raise PackagingTestError(
            f"Console script {name} not found",
            CommandResult(1, "", f"Tried {exe_path}, {cmd_path}, {script_py}"),
        )

    script_path = script_dir / name
    if not script_path.exists():
        raise PackagingTestError(
            f"Console script {name} not found",
            CommandResult(1, "", f"{script_path} does not exist"),
        )

    return _run([str(script_path), *args], env=env)


def _upgrade_venv_tooling(python_bin: Path, script_dir: Path) -> None:
    """Upgrade pip tooling in the created venv to reduce flakiness."""
    result = _run(
        [str(python_bin), "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"],
        env=_venv_env(script_dir),
    )
    if result.returncode != 0:
        raise PackagingTestError("Failed to upgrade pip/setuptools/wheel in venv", result)


def test_wheel_install_no_deps_import_smoke(tmp_path: Path) -> None:
    """STRICT: wheel can be installed with --no-deps and shows clear dependency error."""
    repo_root = Path(__file__).resolve().parents[2]
    dist_dir = tmp_path / "dist"

    wheel_path = _build_wheel(repo_root, dist_dir)
    _, python_bin, pip_bin, script_dir = _create_venv(tmp_path)
    _upgrade_venv_tooling(python_bin, script_dir)

    env = _venv_env(script_dir)
    result = _run([str(pip_bin), "install", "--no-deps", str(wheel_path)], env=env)
    if result.returncode != 0:
        raise PackagingTestError("Failed to install wheel with --no-deps", result)

    # Test that import fails gracefully with clear dependency error
    result = _run([str(python_bin), "-c", "import ai_utilities; print(ai_utilities.__version__)"], env=env)
    if result.returncode == 0:
        raise PackagingTestError("Import should have failed without dependencies", result)
    
    # Verify the error is about missing dependencies, not something else
    assert "ModuleNotFoundError" in result.stderr
    assert "pydantic" in result.stderr or "No module named" in result.stderr


def test_wheel_install_with_deps_cli_help_and_import(tmp_path: Path) -> None:
    """REALISTIC: wheel can be installed normally (with deps) and import/CLI work."""
    repo_root = Path(__file__).resolve().parents[2]
    dist_dir = tmp_path / "dist"

    wheel_path = _build_wheel(repo_root, dist_dir)
    _, python_bin, pip_bin, script_dir = _create_venv(tmp_path)
    _upgrade_venv_tooling(python_bin, script_dir)

    env = _venv_env(script_dir)
    result = _run([str(pip_bin), "install", str(wheel_path)], env=env)
    if result.returncode != 0:
        raise PackagingTestError("Failed to install wheel with dependencies", result)

    result = _run([str(python_bin), "-c", "import ai_utilities; print(ai_utilities.__version__)"], env=env)
    if result.returncode != 0:
        raise PackagingTestError("Failed to import ai_utilities", result)

    result = _run_console_script(script_dir, python_bin, "ai-utilities", "--help")
    if result.returncode != 0:
        raise PackagingTestError("Failed to run ai-utilities --help", result)

    assert result.stdout.strip() != ""
    assert "usage:" in result.stdout.lower()


def test_wheel_install_openai_extra_cli_help_and_openai_provider_import(tmp_path: Path) -> None:
    """EXTRAS: OpenAI dependency present and provider module import works."""
    repo_root = Path(__file__).resolve().parents[2]
    dist_dir = tmp_path / "dist"

    wheel_path = _build_wheel(repo_root, dist_dir)
    _, python_bin, pip_bin, script_dir = _create_venv(tmp_path)
    _upgrade_venv_tooling(python_bin, script_dir)

    env = _venv_env(script_dir)

    result = _run([str(pip_bin), "install", str(wheel_path)], env=env)
    if result.returncode != 0:
        raise PackagingTestError("Failed to install wheel", result)

    # This may require network unless dependency is cached locally.
    result = _run([str(pip_bin), "install", "openai>=1.0,<3"], env=env)
    if result.returncode != 0:
        raise PackagingTestError("Failed to install openai dependency", result)

    result = _run([str(python_bin), "-c", "import ai_utilities; print(ai_utilities.__version__)"], env=env)
    if result.returncode != 0:
        raise PackagingTestError("Failed to import ai_utilities", result)

    result = _run_console_script(script_dir, python_bin, "ai-utilities", "--help")
    if result.returncode != 0:
        raise PackagingTestError("Failed to run ai-utilities --help", result)

    result = _run(
        [str(python_bin), "-c", "import ai_utilities.providers.openai_provider as m; print(m.__name__)"],
        env=env,
    )
    if result.returncode != 0:
        raise PackagingTestError("Failed to import OpenAI provider module", result)

    assert "ai_utilities.providers.openai_provider" in result.stdout
