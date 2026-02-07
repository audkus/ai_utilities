"""Test sdist contents validation."""

from __future__ import annotations

import os
import tarfile
from pathlib import Path
from typing import Iterable, Set

import pytest

pytestmark = pytest.mark.packaging


def _list_sdist_members(tar_gz_path: Path) -> Set[str]:
    """Return all member paths in an sdist tar.gz."""
    members: Set[str] = set()
    with tarfile.open(tar_gz_path, mode="r:gz") as tf:
        for m in tf.getmembers():
            if m.name:
                members.add(m.name)
    return members


def _iter_audio_paths(members: Iterable[str]) -> Iterable[str]:
    for name in members:
        lower = name.lower()
        if lower.endswith(".wav") or lower.endswith(".mp3"):
            yield name


def test_sdist_audio_only_in_examples_assets() -> None:
    """
    Enforce sdist rule:
    - .wav/.mp3 may only appear under examples/assets/
    """
    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    dist = project_root / "dist"
    sdists = sorted(dist.glob("*.tar.gz"))
    assert sdists, f"No sdist found in {dist}/. Run `python -m build` first."
    sdist = sdists[0]

    members = _list_sdist_members(sdist)

    bad: list[str] = []
    for p in _iter_audio_paths(members):
        # sdist has a top folder like ai_utilities-1.0.0/...
        # We accept any prefix as long as the remainder contains examples/assets/
        if "/examples/assets/" not in p.replace("\\", "/"):
            bad.append(p)

    assert not bad, (
        "Audio files must be located under examples/assets/ in the sdist. "
        f"Found audio outside allowed path:\n- " + "\n- ".join(sorted(bad))
    )
