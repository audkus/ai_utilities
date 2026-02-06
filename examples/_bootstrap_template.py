#!/usr/bin/env python3
"""
=== BOOTSTRAP TEMPLATE FOR ALL EXAMPLE SCRIPTS ===

Copy this block to the top of every example script (after the docstring):

# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
from pathlib import Path
import sys

# Get the script's file path and find repo root
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent

# Add src directory to sys.path if not already there
src_dir = repo_root / "src"
src_dir_str = str(src_dir)
if src_dir_str not in sys.path:
    sys.path.insert(0, src_dir_str)

# Add repo root to sys.path for examples import
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

# Import shared helpers
from examples._common import (
    repo_root, assets_dir, output_dir, print_header, require_env, safe_write_bytes
)

# === END BOOTSTRAP ===

This ensures:
1. Scripts can run from anywhere (repo root, subfolder, absolute path)
2. ai_utilities is always importable
3. Shared utilities are available
4. No brittle relative imports
"""
