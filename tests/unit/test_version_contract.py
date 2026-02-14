from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import ai_utilities


def test_package_version_matches_pyproject() -> None:
    # Use relative path from test directory to repo root
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text())
    expected = data["project"]["version"]
    assert ai_utilities.__version__ == expected
