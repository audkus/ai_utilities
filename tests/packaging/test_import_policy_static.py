"""Static analysis tests for import policy compliance."""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Set

import pytest

pytestmark = pytest.mark.packaging


def _find_python_files(src_dir: Path) -> Set[Path]:
    """Find all Python files in source directory."""
    python_files = set()
    for path in src_dir.rglob("*.py"):
        if "__pycache__" not in str(path):
            python_files.add(path)
    return python_files


def _get_imports_from_file(file_path: Path) -> Set[str]:
    """Extract import statements from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Remove comments to avoid picking up commented imports
        lines = []
        for line in content.split("\n"):
            # Remove inline comments
            if "#" in line:
                line = line[:line.index("#")]
            lines.append(line.strip())
        
        clean_content = "\n".join(lines)
        tree = ast.parse(clean_content)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        
        return imports
    except Exception:
        # If we can't parse the file, skip it
        return set()


def _get_optional_dependency_modules() -> Set[str]:
    """Return modules that should be optional dependencies."""
    # These should only be imported lazily or with try/except guards
    # in core modules, but can be imported directly in provider-specific modules
    optional_modules = {
        "openai",  # OpenAI provider
        "anthropic",  # Anthropic provider (if added)
        "ollama",  # Ollama provider (if added)
        "groq",  # Groq provider (if added)
    }
    return optional_modules


def _get_core_optional_modules() -> Set[str]:
    """Return modules that should never be imported at module level in core code."""
    # These should never be imported at module level in core modules
    # (client.py, __init__.py, config_models.py, etc.)
    core_optional = {
        "openai",  # OpenAI provider
        "anthropic",  # Anthropic provider (if added)
        "ollama",  # Ollama provider (if added)
        "groq",  # Groq provider (if added)
        "transformers",  # HuggingFace transformers
        "torch",  # PyTorch
        "tensorflow",  # TensorFlow
        "numpy",  # NumPy (if not core)
        "pandas",  # Pandas (if not core)
        "matplotlib",  # Matplotlib (if not core)
        "seaborn",  # Seaborn (if not core)
        "scipy",  # SciPy (if not core)
        "sklearn",  # Scikit-learn (if not core)
    }
    return core_optional


def _get_core_modules() -> Set[str]:
    """Return modules that should never import optional dependencies at module level."""
    return {
        "src/ai_utilities/__init__.py",
        "src/ai_utilities/client.py", 
        "src/ai_utilities/config_models.py",
        "src/ai_utilities/async_client.py",
        "src/ai_utilities/models.py",
        "src/ai_utilities/exceptions.py",
    }


def test_no_optional_dependency_imports_at_module_level() -> None:
    """
    Test that optional dependencies are not imported at module level in core modules.
    
    This is a lightweight static check for obvious regressions.
    Runtime tests (wheel import smoke test) cover the actual behavior.
    
    Only checks core modules - provider modules can import their dependencies directly.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src/ai_utilities"
    core_optional_modules = _get_core_optional_modules()
    core_modules = _get_core_modules()
    
    violations = []
    
    for py_file in _find_python_files(src_dir):
        # Only check core modules
        relative_path = str(py_file.relative_to(project_root))
        if relative_path not in core_modules:
            continue
            
        imports = _get_imports_from_file(py_file)
        
        for imp in imports:
            # Check for direct imports of optional modules
            imp_parts = imp.split(".")
            if imp_parts[0] in core_optional_modules:
                violations.append(f"{py_file}: imports {imp}")
    
    assert not violations, (
        "Found optional dependency imports at module level in core modules:\n"
        f"- " + "\n- ".join(sorted(violations)) + "\n\n"
        "These should be imported lazily or with try/except guards."
    )


def test_init_module_imports_are_safe() -> None:
    """
    Test that __init__.py doesn't import optional dependencies.
    
    The main __init__.py should be especially careful about imports.
    """

    # Use absolute path from project root
    project_root = Path(__file__).parent.parent.parent
    init_file = project_root / "src/ai_utilities/__init__.py"
    optional_modules = _get_optional_dependency_modules()
    
    assert init_file.exists(), f"__init__.py not found at {init_file}"
    
    imports = _get_imports_from_file(init_file)
    violations = []
    
    for imp in imports:
        imp_parts = imp.split(".")
        if imp_parts[0] in optional_modules:
            violations.append(imp)
    
    assert not violations, (
        f"__init__.py imports optional dependencies:\n"
        f"- " + "\n- ".join(sorted(violations)) + "\n\n"
        "__init__.py must not import optional dependencies at module level."
    )
