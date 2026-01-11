"""Configuration integrity tests to prevent regression.

These tests ensure that we maintain single source of truth for configuration
and prevent accidental re-introduction of conflicting configuration files.
"""

import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Python 3.9 compatibility for TOML parsing
try:
    import tomllib
except ImportError:
    import tomli as tomllib


class TestConfigurationIntegrity:
    """Test configuration integrity to prevent regression."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def pyproject_toml_path(self, project_root: Path) -> Path:
        """Get the pyproject.toml path."""
        return project_root / "pyproject.toml"

    @pytest.fixture
    def pyproject_config(self, pyproject_toml_path: Path) -> Dict[str, Any]:
        """Load and parse pyproject.toml."""
        with open(pyproject_toml_path, "rb") as f:
            return tomllib.load(f)

    def test_no_setup_py_exists(self, project_root: Path):
        """Ensure setup.py does not exist (single source of truth)."""
        setup_py_path = project_root / "setup.py"
        
        assert not setup_py_path.exists(), (
            "setup.py should not exist. "
            "Use pyproject.toml as single source of truth for configuration. "
            f"Remove {setup_py_path}"
        )

    def test_no_pytest_ini_exists(self, project_root: Path):
        """Ensure pytest.ini does not exist (single source of truth)."""
        pytest_ini_path = project_root / "pytest.ini"
        
        assert not pytest_ini_path.exists(), (
            "pytest.ini should not exist. "
            "Use [tool.pytest.ini_options] in pyproject.toml as single source of truth. "
            f"Remove {pytest_ini_path}"
        )

    def test_pyproject_toml_exists(self, project_root: Path):
        """Ensure pyproject.toml exists and is readable."""
        pyproject_toml_path = project_root / "pyproject.toml"
        
        assert pyproject_toml_path.exists(), (
            "pyproject.toml must exist as the single source of truth for configuration"
        )
        
        assert pyproject_toml_path.is_file(), (
            "pyproject.toml must be a file"
        )

    def test_pyproject_toml_valid_syntax(self, pyproject_config: Dict[str, Any]):
        """Ensure pyproject.toml has valid syntax and required sections."""
        # Check build system
        assert "build-system" in pyproject_config, (
            "pyproject.toml must have [build-system] section"
        )
        
        build_system = pyproject_config["build-system"]
        assert "requires" in build_system, (
            "[build-system] must have 'requires' field"
        )
        assert "build-backend" in build_system, (
            "[build-system] must have 'build-backend' field"
        )

    def test_pyproject_toml_project_metadata(self, pyproject_config: Dict[str, Any]):
        """Ensure pyproject.toml has complete project metadata."""
        assert "project" in pyproject_config, (
            "pyproject.toml must have [project] section"
        )
        
        project = pyproject_config["project"]
        required_fields = ["name", "version", "description", "requires-python"]
        
        for field in required_fields:
            assert field in project, (
                f"[project] must have '{field}' field"
            )

    def test_pyproject_toml_pytest_configuration(self, pyproject_config: Dict[str, Any]):
        """Ensure pyproject.toml has proper pytest configuration."""
        assert "tool" in pyproject_config, (
            "pyproject.toml must have [tool] section"
        )
        
        tool = pyproject_config["tool"]
        assert "pytest" in tool or "pytest.ini_options" in tool, (
            "pyproject.toml must have [tool.pytest.ini_options] section for pytest configuration"
        )
        
        # Handle both possible pytest configuration locations
        pytest_config = tool.get("pytest", {})
        if "ini_options" in pytest_config:
            pytest_config = pytest_config["ini_options"]
        elif "pytest.ini_options" in tool:
            pytest_config = tool["pytest.ini_options"]
        
        # Check essential pytest configuration
        assert "testpaths" in pytest_config, (
            "[tool.pytest.ini_options] must have 'testpaths' field"
        )
        assert pytest_config["testpaths"] == ["tests"], (
            "testpaths should be ['tests'] to restrict test discovery"
        )

    def test_pyproject_toml_consistent_naming(self, pyproject_config: Dict[str, Any]):
        """Ensure consistent naming in pyproject.toml."""
        project = pyproject_config["project"]
        name = project["name"]
        
        # Should use hyphen consistently (PyPI standard)
        assert "-" in name or "_" not in name, (
            "Package name should use hyphens consistently (PyPI standard), not underscores"
        )
        
        # Version should follow semantic versioning
        version = project["version"]
        assert isinstance(version, str), (
            "Version must be a string"
        )
        
        # Check version format (should be semantic with optional beta suffix)
        import re
        version_pattern = r'^\d+\.\d+\.\d+(?:b\d+)?$'
        assert re.match(version_pattern, version), (
            f"Version '{version}' should follow semantic versioning (e.g., '1.0.0' or '1.0.0b2')"
        )

    def test_no_legacy_configuration_files(self, project_root: Path):
        """Ensure no other legacy configuration files exist."""
        legacy_files = [
            "setup.cfg",
            "tox.ini",  # Can be kept but should be documented
            "setup.cfg",  # Legacy setuptools configuration
        ]
        
        for legacy_file in legacy_files:
            file_path = project_root / legacy_file
            if legacy_file == "tox.ini":
                # tox.ini is acceptable but should be documented
                continue
                
            assert not file_path.exists(), (
                f"Legacy configuration file '{legacy_file}' should not exist. "
                f"Use pyproject.toml as single source of truth. "
                f"Remove {file_path}"
            )

    def test_pyproject_toml_modern_python_version(self, pyproject_config: Dict[str, Any]):
        """Ensure pyproject.toml specifies modern Python version."""
        project = pyproject_config["project"]
        requires_python = project["requires-python"]
        
        # Should require Python 3.9 or newer (modern standard)
        assert ">=3.9" in requires_python, (
            f"requires-python should be '>=3.9' or newer, got '{requires_python}'"
        )
        
        # Should not support very old Python versions
        assert "3.8" not in requires_python, (
            "should not support Python 3.8 (use modern Python 3.9+)"
        )

    def test_pyproject_toml_build_backend(self, pyproject_config: Dict[str, Any]):
        """Ensure pyproject.toml uses modern build backend."""
        build_system = pyproject_config["build-system"]
        build_backend = build_system["build-backend"]
        
        assert build_backend == "setuptools.build_meta", (
            f"build-backend should be 'setuptools.build_meta', got '{build_backend}'"
        )

    def test_directory_structure_clean(self, project_root: Path):
        """Ensure project directory structure is clean and organized."""
        # Check for common project structure
        expected_dirs = [
            "src",
            "tests", 
            "examples",
            "docs",
        ]
        
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), (
                f"Expected directory '{dir_name}' should exist"
            )
            assert dir_path.is_dir(), (
                f"'{dir_name}' should be a directory"
            )

    def test_no_duplicate_test_files_outside_tests(self, project_root: Path):
        """Ensure no test files exist outside the tests/ directory."""
        test_patterns = ["test_*.py", "*_test.py"]
        
        # Check common directories that shouldn't contain test files
        check_dirs = ["src", "examples", "scripts", "manual_tests"]
        
        for check_dir in check_dirs:
            dir_path = project_root / check_dir
            if not dir_path.exists():
                continue
                
            for pattern in test_patterns:
                test_files = list(dir_path.glob(pattern))
                assert len(test_files) == 0, (
                    f"Found test files {test_files} in {check_dir}/. "
                    f"All test files should be in tests/ directory. "
                    f"Move or remove these files."
                )


class TestConfigurationBestPractices:
    """Test configuration best practices for maintainability."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_pyproject_toml_well_structured(self, project_root: Path):
        """Ensure pyproject.toml is well-structured and readable."""
        pyproject_path = project_root / "pyproject.toml"
        
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have proper section comments (optional but good practice)
        lines = content.split('\n')
        
        # Check for essential sections
        assert '[build-system]' in content, (
            "Missing [build-system] section"
        )
        assert '[project]' in content, (
            "Missing [project] section"
        )
        assert '[tool.pytest.ini_options]' in content, (
            "Missing [tool.pytest.ini_options] section"
        )

    def test_gitignore_prevents_committing_bad_files(self, project_root: Path):
        """Ensure .gitignore prevents committing problematic files."""
        gitignore_path = project_root / ".gitignore"
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            
            # Should ignore common build artifacts
            ignored_patterns = [
                "__pycache__/",
                "*.pyc",
                "build/",
                "dist/",
                "*.egg-info/",
            ]
            
            for pattern in ignored_patterns:
                assert pattern in gitignore_content, (
                    f".gitignore should include '{pattern}' to ignore build artifacts"
                )

    def test_readme_mentions_configuration(self, project_root: Path):
        """Ensure README mentions the configuration approach."""
        readme_path = project_root / "README.md"
        
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read().lower()
            
            # Should mention pyproject.toml or modern configuration
            assert "pyproject.toml" in readme_content or "configuration" in readme_content, (
                "README should mention the use of pyproject.toml for configuration"
            )


if __name__ == "__main__":
    # Run these tests directly to check configuration integrity
    pytest.main([__file__, "-v"])
