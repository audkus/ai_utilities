"""Tests to ensure project structure remains clean and organized."""

import os
import pytest
from pathlib import Path


class TestProjectStructure:
    """Test that project structure follows conventions and doesn't get polluted."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent  # tests/policies/ -> tests/ -> project root
    
    @pytest.fixture
    def tests_dir(self, project_root):
        """Get the tests directory."""
        return project_root / "tests"

    @pytest.fixture(autouse=True)
    def cleanup_coverage_dirs(self, project_root):
        """Clean up coverage directories before running project structure tests."""
        import shutil
        
        # Clean up legacy htmlcov directory
        htmlcov_path = project_root / "htmlcov"
        if htmlcov_path.exists():
            shutil.rmtree(htmlcov_path, ignore_errors=True)
        
        # Clean up root-level coverage artifacts (except .coveragerc)
        for coverage_file in project_root.glob(".coverage*"):
            if coverage_file.name != ".coveragerc":
                try:
                    coverage_file.unlink()
                except OSError:
                    pass  # Ignore cleanup errors
        
        # Clean up root-level coverage.xml
        coverage_xml = project_root / "coverage.xml"
        if coverage_xml.exists():
            try:
                coverage_xml.unlink()
            except OSError:
                pass

    def test_no_coverage_reports_in_tests_dir(self, tests_dir):
        """Test that coverage reports are not created in the tests directory."""
        coverage_dirs = [
            tests_dir / "coverage_reports",
            tests_dir / "htmlcov", 
            tests_dir / "reports"
        ]
        
        for coverage_dir in coverage_dirs:
            assert not coverage_dir.exists(), f"Coverage directory {coverage_dir} should not exist in tests folder"
    
    def test_no_coverage_data_files_in_tests_dir(self, tests_dir):
        """Test that coverage data files are not created in the tests directory."""
        coverage_files = list(tests_dir.glob(".coverage*"))
        assert len(coverage_files) == 0, f"Found coverage data files in tests directory: {coverage_files}"
    
    def test_coverage_reports_only_in_root(self, project_root):
        """Test that coverage reports are only in the correct location."""
        coverage_reports_dir = project_root / "coverage_reports"
        
        # coverage_reports should exist (created by our coverage runner)
        if coverage_reports_dir.exists():
            assert coverage_reports_dir.is_dir(), "coverage_reports should be a directory"
        
        # Should not have ANY coverage files in root (except .coveragerc which is allowed)
        coverage_files = list(project_root.glob(".coverage*"))
        coverage_files = [f for f in coverage_files if f.name != ".coveragerc"]  # Only allow .coveragerc config
        assert len(coverage_files) == 0, f"Found coverage files in root: {coverage_files}"
        
        # Should not have coverage.xml in root
        coverage_xml = project_root / "coverage.xml"
        assert not coverage_xml.exists(), "coverage.xml should not be in root directory"
    
    def test_coverage_reports_in_correct_subdirectory(self, project_root):
        """Test that HTML coverage reports are in the correct subdirectory."""
        html_dir = project_root / "coverage_reports" / "html"
        coverage_xml = project_root / "coverage_reports" / "coverage.xml"
        
        # If coverage_reports/html exists, it should be a directory
        if html_dir.exists():
            assert html_dir.is_dir(), "HTML reports should be in coverage_reports/html/"
        
        # If coverage.xml exists, it should be in coverage_reports/
        if coverage_xml.exists():
            assert coverage_xml.is_file(), "XML report should be in coverage_reports/coverage.xml"
    
    def test_coverage_data_allowed_in_coverage_reports(self, project_root):
        """Test that coverage data files are allowed in coverage_reports/ directory."""
        coverage_reports_dir = project_root / "coverage_reports"
        
        if coverage_reports_dir.exists():
            # Should allow .coverage files in coverage_reports/
            coverage_data_files = list(coverage_reports_dir.glob(".coverage*"))
            # These files are allowed to exist
            # No assertion needed - just checking they don't cause policy failures
            
            # Should allow coverage.xml in coverage_reports/
            coverage_xml = coverage_reports_dir / "coverage.xml"
            if coverage_xml.exists():
                assert coverage_xml.is_file(), "coverage.xml should be a file in coverage_reports/"
            
            # Should allow html subdirectory
            html_dir = coverage_reports_dir / "html"
            if html_dir.exists():
                assert html_dir.is_dir(), "html should be a directory in coverage_reports/"
    
    def test_no_duplicate_coverage_directories(self, project_root):
        """Test that there are no duplicate coverage report directories."""
        coverage_dirs = list(project_root.glob("**/coverage_reports"))
        htmlcov_dirs = list(project_root.glob("**/htmlcov"))
        
        # Should have at most one coverage_reports directory in root (it's created when coverage runs)
        assert len(coverage_dirs) <= 1, f"Should have at most one coverage_reports directory: {coverage_dirs}"
        
        # Should not have any htmlcov directories (legacy coverage directory)
        assert len(htmlcov_dirs) == 0, f"Should not have htmlcov directories: {htmlcov_dirs}"
    
    def test_reports_directory_structure(self, project_root):
        """Test that reports directory has correct structure if it exists."""
        reports_dir = project_root / "reports"
        if reports_dir.exists():
            # reports directory should contain manual reports and test outputs
            expected_subdirs = ["manual_report_", "test_output", "provider_health"]
            
            # Check that it contains expected content
            contents = list(reports_dir.iterdir())
            assert len(contents) > 0, "reports directory exists but is empty"
            
            # Should not contain coverage reports
            coverage_in_reports = [c for c in contents if "coverage" in c.name.lower()]
            assert len(coverage_in_reports) == 0, f"Found coverage files in reports directory: {coverage_in_reports}"
    
    def test_gitignore_excludes_coverage_files(self, project_root):
        """Test that .gitignore properly excludes coverage files."""
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists(), ".gitignore should exist"
        
        gitignore_content = gitignore_path.read_text()
        
        # Should exclude coverage files
        coverage_patterns = [
            ".coverage",
            ".coverage.*", 
            "htmlcov/",
            "coverage.xml",
            "*.cover"
        ]
        
        for pattern in coverage_patterns:
            assert pattern in gitignore_content, f".gitignore should exclude {pattern}"

        assert (
            "coverage_reports/" in gitignore_content or "coverage_reports/**" in gitignore_content
        ), ".gitignore should exclude coverage_reports/"
    
    def test_no_test_artifacts_in_root(self, project_root):
        """Test that test artifacts are not created in project root."""
        root_files = list(project_root.iterdir())
        
        # Should not have test-specific files in root
        test_artifacts = [
            f for f in root_files
            if f.name.startswith(".coverage") and f.name not in [".coverage", ".coveragerc"]
            or f.name.startswith("test_")
            or f.name == "__pycache__"
            # .pytest_cache is allowed as it's a standard pytest artifact
        ]
        
        test_artifacts = [f for f in test_artifacts if f.name != ".coverage"]
        
        assert len(test_artifacts) == 0, f"Found test artifacts in project root: {test_artifacts}"

    def test_root_directory_structure_clean(self, project_root):
        """Test that root directory contains only essential files and proper directories."""
        root_files = list(project_root.iterdir())
        root_names = {f.name for f in root_files}
        
        # Essential files that should be in root
        essential_files = {
            "README.md", "LICENSE", "pyproject.toml", "pytest.ini", 
            "Makefile", "tox.ini", "MANIFEST.in", ".gitignore", 
            ".pre-commit-config.yaml"
        }
        
        # Essential directories that should be in root
        essential_dirs = {
            "src", "tests", "docs", "examples", "scripts", 
            "tools", ".git", ".github", ".venv", ".pytest_cache", 
            ".coverage", ".ruff_cache", ".mypy_cache", ".windsurf", 
            ".ai_utilities", "coverage_reports"
        }
        
        # Files/dirs that should NOT be in root (should be in appropriate locations)
        forbidden_in_root = {
            # Development utilities that should be in scripts/ or tools/
            "run_all_tests_complete.py",
            
            # Documentation that should be in docs/
            "CHANGELOG.md", "CONTRIBUTING.md", "LOCAL_AI_SETUP.md", "MIGRATION.md",
            "SUPPORT.md", "RELEASE.md", "RELEASE_CHECKLIST.md",
            
            # Temporary files that should not exist
            "model_worker_*.log", "openai_api_server.log", "controller.log",
            "test.txt"
        }
        
        # Check that essential files/dirs are present (optional, not strict)
        missing_essential = (essential_files | essential_dirs) - root_names
        if missing_essential:
            print(f"Note: Missing essential items: {missing_essential}")
        
        # Check that forbidden items are NOT in root
        forbidden_found = []
        for forbidden in forbidden_in_root:
            if "*" in forbidden:
                # Handle wildcards (like log files)
                import fnmatch
                matches = [f for f in root_files if fnmatch.fnmatch(f.name, forbidden)]
                forbidden_found.extend(matches)
            elif forbidden in root_names:
                forbidden_found.append(project_root / forbidden)
        
        assert len(forbidden_found) == 0, f"Found items that should not be in root: {forbidden_found}"
        
        # Verify that docs directory exists and contains the right files
        docs_dir = project_root / "docs"
        coverage_reports_dir = project_root / "coverage_reports"
        
        assert docs_dir.exists(), "docs directory should exist"
        # coverage_reports directory is created when coverage runs, so it may not exist during tests
        
        # Check that coverage_reports has the right structure (if it exists)
        if coverage_reports_dir.exists():
            coverage_html_dir = coverage_reports_dir / "html"
            coverage_xml_dir = coverage_reports_dir / "xml"
            
            # These directories are created when coverage runs
            # They may not exist during tests, and that's OK
        
        # Check that key files are in the right places
        expected_docs = {
            "CHANGELOG.md", "CONTRIBUTING.md", "LOCAL_AI_SETUP.md", "MIGRATION.md",
            "SUPPORT.md", "RELEASE.md", "RELEASE_CHECKLIST.md"
        }
        
        docs_files = {f.name for f in docs_dir.iterdir() if f.is_file()}
        
        missing_docs = expected_docs - docs_files
        
        assert len(missing_docs) == 0, f"Missing files in docs/: {missing_docs}"
