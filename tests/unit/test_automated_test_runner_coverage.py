"""Tests for coverage artifact cleanup in automated_test_runner."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.automated_test_runner import AutomatedTestRunner


class TestCoverageCleanup:
    """Test coverage artifact cleanup functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_tmp_path(self, tmp_path):
        """Setup tmp_path for all tests in this class."""
        self.tmp_path = tmp_path
    
    def test_finalize_coverage_removes_all_files(self):
        """Test that _finalize_coverage removes all .coverage* files."""
        # Create fake coverage files in tmp_path instead of repo root
        test_files = []
        coverage_files = [
            ".coverage.test1.12345.abc",
            ".coverage.test2.67890.def", 
            ".coverage.localhost.99999.xyz"
        ]
        
        try:
            for file_name in coverage_files:
                test_file = self.tmp_path / file_name
                test_file.touch()
                test_files.append(test_file)
            
            # Verify files exist
            for test_file in test_files:
                assert test_file.exists()
            
            # Create runner and monkeypatch its project_root attribute
            runner = AutomatedTestRunner()
            runner.project_root = self.tmp_path
            runner._finalize_coverage()
                
            # Files should be removed
            for test_file in test_files:
                assert not test_file.exists(), f"{test_file.name} should be removed"
                
        finally:
            # Clean up any remaining test files
            for test_file in test_files:
                if test_file.exists():
                    test_file.unlink()
    
    def test_finalize_coverage_preserves_coveragerc(self):
        """Test that .coveragerc is preserved."""
        # Use tmp_path to avoid writing to repo root
        tmp_coveragerc = Path(__file__).resolve().parents[2] / ".coveragerc"
        
        # Copy real .coveragerc to tmp_path if it exists, otherwise create minimal one
        if tmp_coveragerc.exists():
            coveragerc_content = tmp_coveragerc.read_text()
        else:
            coveragerc_content = "[coverage]\n"
        
        # Create a temporary .coveragerc in tmp_path
        tmp_path_coveragerc = self.tmp_path / ".coveragerc"
        tmp_path_coveragerc.write_text(coveragerc_content)
        
        # Create runner and monkeypatch its project_root attribute
        runner = AutomatedTestRunner()
        runner.project_root = self.tmp_path
        runner._finalize_coverage()
        
        # .coveragerc should be preserved in tmp_path
        assert tmp_path_coveragerc.exists(), ".coveragerc should be preserved"
        # Content should be unchanged
        assert tmp_path_coveragerc.read_text() == coveragerc_content
    
    def test_finalize_coverage_creates_directories(self):
        """Test that coverage directories are created."""
        # Create runner and monkeypatch its project_root attribute
        runner = AutomatedTestRunner()
        runner.project_root = self.tmp_path
        runner._finalize_coverage()
        
        # Verify directories are created in tmp_path
        assert (self.tmp_path / "coverage_reports").exists()
        assert (self.tmp_path / "coverage_reports" / "html").exists()
        assert (self.tmp_path / "coverage_reports" / "xml").exists()
    
    def test_finalize_coverage_handles_no_files_gracefully(self):
        """Test cleanup when no coverage files exist."""
        # Create runner and run cleanup - should not fail
        runner = AutomatedTestRunner()
        runner._finalize_coverage()
        
        # Should complete without error
        assert True
