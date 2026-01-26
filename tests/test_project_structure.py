"""Tests to ensure project structure remains clean and organized."""

import os
import pytest
from pathlib import Path


class TestProjectStructure:
    """Test that project structure follows conventions and doesn't get polluted."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def tests_dir(self, project_root):
        """Get the tests directory."""
        return project_root / "tests"
    
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
        """Test that coverage reports exist only in the correct root location."""
        # The correct location should exist
        correct_coverage_dir = project_root / "coverage_reports"
        assert correct_coverage_dir.exists(), "Coverage reports directory should exist at project root"
        
        # Other locations should not exist
        incorrect_locations = [
            project_root / "tests" / "coverage_reports",
            project_root / "tests" / "htmlcov",
            project_root / "htmlcov"  # This should be coverage_reports/html
        ]
        
        for location in incorrect_locations:
            assert not location.exists(), f"Coverage directory {location} should not exist"
    
    def test_coverage_html_in_correct_subdirectory(self, project_root):
        """Test that HTML coverage reports are in the correct subdirectory."""
        html_dir = project_root / "coverage_reports" / "html"
        # This might not exist if no HTML report has been generated, but if it exists,
        # it should be in the right place
        if html_dir.exists():
            assert html_dir.is_dir(), "HTML reports should be in coverage_reports/html/"
    
    def test_no_duplicate_coverage_directories(self, project_root):
        """Test that there are no duplicate coverage report directories."""
        coverage_dirs = list(project_root.glob("**/coverage_reports"))
        htmlcov_dirs = list(project_root.glob("**/htmlcov"))
        
        # Should only have one coverage_reports directory at root
        assert len(coverage_dirs) == 1, f"Found multiple coverage_reports directories: {coverage_dirs}"
        assert coverage_dirs[0] == project_root / "coverage_reports", "coverage_reports should be at root"
        
        # Should not have any htmlcov directories (use coverage_reports/html instead)
        assert len(htmlcov_dirs) == 0, f"Found htmlcov directories (should use coverage_reports/html): {htmlcov_dirs}"
    
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
    
    def test_coverage_reports_gitignore(self, project_root):
        """Test that coverage_reports/.gitignore is properly configured."""
        coverage_gitignore = project_root / "coverage_reports" / ".gitignore"
        assert coverage_gitignore.exists(), "coverage_reports/.gitignore should exist"
        
        content = coverage_gitignore.read_text().strip()
        # Should ignore everything except .gitignore itself
        assert content == "*", f"coverage_reports/.gitignore should contain '*', got: {content}"
    
    def test_no_test_artifacts_in_root(self, project_root):
        """Test that test artifacts are not created in project root."""
        root_files = list(project_root.iterdir())
        
        # Should not have test-specific files in root
        test_artifacts = [
            f for f in root_files 
            if f.name.startswith(".coverage") and f.name != ".coverage"
            or f.name.startswith("test_")
            or f.name == "__pycache__"
            # .pytest_cache is allowed as it's a standard pytest artifact
        ]
        
        # Allow .coverage in root (that's the correct location)
        test_artifacts = [f for f in test_artifacts if f.name != ".coverage"]
        
        assert len(test_artifacts) == 0, f"Found test artifacts in project root: {test_artifacts}"
